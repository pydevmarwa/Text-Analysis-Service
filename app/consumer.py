import asyncio
import json
import aio_pika
from aio_pika import RobustConnection
from app.config import RABBITMQ
from app.processor import process_message
from app.db import save_to_mongodb
from app.publisher import publish_result
from app.logger import logger

async def connect_with_retry(retries=10, delay=3) -> RobustConnection:
    """
    Connects to RabbitMQ with retry logic in case of failure.

    Args:
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.

    Returns:
        RobustConnection: Established robust connection to RabbitMQ.
    """
    logger.info("Starting RabbitMQ connection attempts")
    for attempt in range(1, retries + 1):
        try:
            connection: RobustConnection = await aio_pika.connect_robust(
                host=RABBITMQ["HOST"],
                port=RABBITMQ["PORT"],
                login=RABBITMQ["USER"],
                password=RABBITMQ["PASSWORD"],
            )
            logger.info("Connected to RabbitMQ")
            return connection
        except Exception as e:
            logger.error(f"Connection attempt {attempt} failed: {e}")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)

async def handle_message(message: aio_pika.IncomingMessage):
    """
    Process a single incoming message from RabbitMQ.

    Args:
        message (aio_pika.IncomingMessage): Incoming message instance.
    """
    async with message.process(requeue=False):
        try:
            raw_data = json.loads(message.body.decode())
            logger.info(f"Received message {raw_data.get('id')}")

            processed = await process_message(raw_data)
            await save_to_mongodb(processed)

            if processed.get("action") != "delete":
                await publish_result(processed)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received, message will be NACKed")
            raise
        except Exception as e:
            logger.exception(f"Error processing message, message will be NACKed: {e}")
            raise

async def start_consumer():
    """
    Starts the RabbitMQ consumer to listen for incoming messages asynchronously.

    Returns:
        RobustConnection: The connection object to RabbitMQ.
    """
    connection = await connect_with_retry()
    channel = await connection.channel()

    # Process up to 20 messages concurrently
    await channel.set_qos(prefetch_count=20)

    queue = await channel.declare_queue(RABBITMQ["INPUT_QUEUE"], durable=True)
    logger.info("Waiting for messages...")

    async def on_message(message: aio_pika.IncomingMessage):
        asyncio.create_task(handle_message(message))

    await queue.consume(on_message)
    return connection
