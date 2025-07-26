import json
from aio_pika import connect_robust, Message, DeliveryMode
from app.config import RABBITMQ
from app.logger import logger

async def publish_result(processed_message: dict):
    """
    Publish the processed message to the output RabbitMQ queue.

    Args:
        processed_message (dict): Message to publish.
    """
    if processed_message.get('action') == 'delete':
        logger.debug(f"Skipping publish for delete id={processed_message.get('id')}")
        return  # Do not publish deletions

    connection = await connect_robust(
        host=RABBITMQ['HOST'],
        port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'],
        password=RABBITMQ['PASSWORD'],
    )
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(RABBITMQ['OUTPUT_QUEUE'], durable=True)

        await channel.default_exchange.publish(
            Message(
                body=json.dumps(processed_message).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=RABBITMQ['OUTPUT_QUEUE']
        )
        logger.info(f"Published processed message id={processed_message.get('id')}")

