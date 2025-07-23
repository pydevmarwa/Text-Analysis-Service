import asyncio
import sys
import json
from datetime import datetime

import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import RABBITMQ, MONGO

BATCH_SIZE = 500
DELETE_EVERY = 5
EXPECTED_UPDATES = BATCH_SIZE - (BATCH_SIZE // DELETE_EVERY)

INPUT_QUEUE = RABBITMQ['INPUT_QUEUE']
OUTPUT_QUEUE = RABBITMQ['OUTPUT_QUEUE']


async def clear_db():
    """
    Empty the MongoDB collection to start from a clean state.
    """
    client = AsyncIOMotorClient(MONGO['URI'])
    col = client[MONGO['DB_NAME']][MONGO['COLLECTION']]
    await col.delete_many({})
    client.close()
    print("[*] MongoDB cleared.")


async def purge_output_queue():
    """
    Purge the OUTPUT_QUEUE so it starts empty.
    """
    conn = await aio_pika.connect_robust(
        host=RABBITMQ['HOST'], port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'], password=RABBITMQ['PASSWORD']
    )
    async with conn:
        ch = await conn.channel()
        q = await ch.declare_queue(OUTPUT_QUEUE, durable=True)
        await q.purge()
        print(f"[*] Queue '{OUTPUT_QUEUE}' purged.")


async def publish_batch():
    """
    Publish BATCH_SIZE messages (mix of update/delete) to the input queue.
    """
    conn = await aio_pika.connect_robust(
        host=RABBITMQ['HOST'], port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'], password=RABBITMQ['PASSWORD']
    )
    async with conn:
        ch = await conn.channel()
        await ch.declare_queue(INPUT_QUEUE, durable=True)

        for i in range(BATCH_SIZE):
            action = "delete" if i % DELETE_EVERY == 0 else "update"
            msg = {
                "id": f"msg_{i}",
                "user_id": f"user_{i % 20}",  #Simulate multiple updates for same users
                "timestamp": datetime.utcnow().isoformat(),
                "type": action
            }
            if action == "update":
                msg["text"] = f"Test message {i}"
            await ch.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(msg).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=INPUT_QUEUE
            )
        print(f"[+] Published {BATCH_SIZE} messages ({EXPECTED_UPDATES} updates, {BATCH_SIZE//DELETE_EVERY} deletes).")


async def wait_for_db():
    """
    Wait indefinitely until MongoDB has EXPECTED_UPDATES documents.
    """
    client = AsyncIOMotorClient(MONGO['URI'])
    col = client[MONGO['DB_NAME']][MONGO['COLLECTION']]
    while True:
        count = await col.count_documents({})
        print(f"    [DB] {count}/{EXPECTED_UPDATES}")
        if count >= EXPECTED_UPDATES:
            client.close()
            print("MongoDB has all expected documents.")
            return
        await asyncio.sleep(2)


async def peek_output_queue():
    """
    Peek all messages in OUTPUT_QUEUE without ack, print them,
    then close connection so they requeue.
    Returns list of message dicts.
    """
    conn = await aio_pika.connect_robust(
        host=RABBITMQ['HOST'], port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'], password=RABBITMQ['PASSWORD']
    )
    received = []
    async with conn:
        ch = await conn.channel()
        q = await ch.declare_queue(OUTPUT_QUEUE, durable=True)
        print("[*] Peeking into output queue:")
        while True:
            msg = await q.get(no_ack=False, fail=False)
            if msg is None:
                break
            data = json.loads(msg.body.decode())
            print("  ›", json.dumps(data))
            received.append(data)
        print("[*] End of queue peek (messages requeued).")
    return received


async def main():
    # 1) Clear DB and queue
    await clear_db()
    await purge_output_queue()

    # 2) Publish batch
    await publish_batch()

    # 3) Wait for DB to be populated
    print("[*] Waiting for MongoDB to record all updates...")
    await wait_for_db()

    # 4) Peek the output queue until we have all messages
    outputs = []
    while len(outputs) < EXPECTED_UPDATES:
        outputs = await peek_output_queue()
        if len(outputs) < EXPECTED_UPDATES:
            print(f"[!] Only {len(outputs)}/{EXPECTED_UPDATES} messages peeked, retrying in 2s...")
            await asyncio.sleep(2)

    # 5) Final report
    print(f"END-TO-END FUNCTIONAL TEST PASSED: peeked {len(outputs)} messages.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
