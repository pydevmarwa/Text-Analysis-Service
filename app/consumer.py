import asyncio
import json

from aio_pika import connect_robust, IncomingMessage
from app.processor import process_message
from app.db import save_to_mongodb
from app.publisher import publish_result
from app.config import RABBITMQ, PROCESSING
from app.logger import logger

# Concurrency control semaphore
SEMAPHORE = asyncio.Semaphore(PROCESSING['MAX_CONCURRENT_TASKS'])

async def connect_with_retry(retries: int = 10, delay: int = 3):
    logger.info("Connecting to RabbitMQ...")
    for attempt in range(1, retries + 1):
        try:
            connection = await connect_robust(
                host=RABBITMQ['HOST'],
                port=RABBITMQ['PORT'],
                login=RABBITMQ['USER'],
                password=RABBITMQ['PASSWORD'],
            )
            logger.info("Connected to RabbitMQ on attempt %d", attempt)
            return connection
        except Exception as e:
            logger.error("Connection attempt %d/%d failed: %s", attempt, retries, e)
            if attempt == retries:
                raise
            await asyncio.sleep(delay)

async def handle_message(msg: IncomingMessage):
    async with SEMAPHORE:  # Limit concurrent processing
        async with msg.process(requeue=False):
            deaths = msg.headers.get('x-death', [])
            retry_count = deaths[0]['count'] if deaths else 0

            if retry_count >= RABBITMQ['MAX_RETRIES']:
                logger.error("[DLX] Max retries reached for %s", msg.message_id)
                return

            try:
                raw = json.loads(msg.body.decode())
                logger.info("Received message %s (attempt %d)", raw.get('id'), retry_count + 1)

                # Process message
                processed = await process_message(raw)
                # Store processed result
                await save_to_mongodb(processed)

                # Only publish if not a delete action
                if processed.get('action') != 'delete':
                    await publish_result(processed)

                logger.info("Message %s processed successfully", raw.get('id'))

            except json.JSONDecodeError:
                logger.warning("Invalid JSON, message will be NACKed: %s", msg.body)
                raise  # Will trigger NACK and retry
            except Exception:
                logger.exception("Error processing message, will retry")
                await msg.nack(requeue=True)

async def start_consumer():
    connection = await connect_with_retry(
        retries=RABBITMQ.get('RETRY_ATTEMPTS', 10),
        delay=RABBITMQ.get('RETRY_DELAY', 3)
    )
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=RABBITMQ['PREFETCH_COUNT'])

    # Declare queue with DLX support
    await channel.declare_queue(
        RABBITMQ['INPUT_QUEUE'],
        durable=True,
        arguments={"x-dead-letter-exchange": RABBITMQ['DLX_EXCHANGE']}
    )
    queue = await channel.get_queue(RABBITMQ['INPUT_QUEUE'])
    await queue.consume(handle_message, no_ack=False)

    logger.info("Consumer ready, listening on %s", RABBITMQ['INPUT_QUEUE'])
    return connection
