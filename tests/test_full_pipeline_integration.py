import asyncio
import json
from datetime import datetime

import pytest
import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import RABBITMQ, MONGO
from app.consumer import start_consumer

# Configuration for the test
BATCH_SIZE = 300
DELETE_EVERY = 5
EXPECTED_UPDATES = BATCH_SIZE - (BATCH_SIZE // DELETE_EVERY)

@pytest.mark.asyncio
async def test_full_pipeline_integration():
    """
    End-to-end integration test:
    - Starts the real consumer service
    - Publishes a batch of messages to RabbitMQ
    - Verifies MongoDB was updated accordingly
    - Verifies the expected messages were published in the output queue
    """

    # 1. Start the actual consumer (which handles consuming, processing, storing, and publishing)
    consumer_conn = await start_consumer()
    await asyncio.sleep(1)  # Allow the consumer to fully initialize

    # 2. Establish connection to RabbitMQ and declare the queues
    rmq = await aio_pika.connect_robust(
        host=RABBITMQ['HOST'],
        port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'],
        password=RABBITMQ['PASSWORD'],
    )
    ch = await rmq.channel()
    await ch.set_qos(prefetch_count=20)
    in_q = await ch.declare_queue(RABBITMQ['INPUT_QUEUE'], durable=True, passive=True)
    out_q = await ch.declare_queue(RABBITMQ['OUTPUT_QUEUE'], durable=True)

    # 3. Clean up any previous state: MongoDB documents and RabbitMQ queues
    mongo = AsyncIOMotorClient(MONGO['URI'])
    col = mongo[MONGO['DB_NAME']][MONGO['COLLECTION']]
    await col.delete_many({})
    await in_q.purge()
    await out_q.purge()

    # 4. Publish BATCH_SIZE messages (some 'update', some 'delete') to the input queue
    for i in range(BATCH_SIZE):
        action = 'delete' if i % DELETE_EVERY == 0 else 'update'
        msg = {
            'id':        f'msg_{i}',
            'text':      f'Test {i}',
            'user_id':   'test_user',
            'timestamp': datetime.utcnow().isoformat(),
            'type':      action
        }
        await ch.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(msg).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=RABBITMQ['INPUT_QUEUE']
        )

    # 5. Wait until all expected updates are stored in MongoDB
    cnt = await col.count_documents({})
    while cnt < EXPECTED_UPDATES:
        await asyncio.sleep(1)
        cnt = await col.count_documents({})

    assert cnt == EXPECTED_UPDATES, f"MongoDB expected {EXPECTED_UPDATES}, got {cnt}"

    # 6. Consume messages from output queue and verify that only updates were published
    received = []
    while len(received) < EXPECTED_UPDATES:
        msg = await out_q.get(no_ack=False, fail=False)
        if msg is None:
            # Output queue temporarily empty — wait and retry
            await asyncio.sleep(0.5)
            continue
        data = json.loads(msg.body.decode())
        received.append(data)
        # We don't ack here to simulate connection close behavior (auto requeue on disconnect)

    # 7. Check that the number of messages and their actions are correct
    assert len(received) == EXPECTED_UPDATES
    assert all(m['action'] == 'update' for m in received)

    # 8. Cleanup connections
    await rmq.close()
    await consumer_conn.close()
    mongo.close()
