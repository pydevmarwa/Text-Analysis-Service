import os
import asyncio
import signal
from app.consumer import start_consumer
from app.db import db_manager
from app.logger import logger

async def shutdown(signal_name: str, connection):
    """
    Gracefully shutdown on SIGTERM or SIGINT.
    """
    logger.info(f"Received {signal_name}, shutting down...")
    await db_manager.close()
    if connection:
        await connection.close()
    logger.info("Connections closed. Service shutdown complete.")
    # Stop the loop
    asyncio.get_event_loop().stop()

async def main():
    logger.info("Starting Text Analysis Service")
    connection = None

    # Install signal handlers for SIGTERM and SIGINT
    loop = asyncio.get_event_loop()
    for s in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            s,
            lambda s=s: asyncio.create_task(shutdown(s.name, connection))
        )

    try:
        consumer = await asyncio.gather(
            *(start_consumer() for _ in range(int(os.getenv("NUM_CONSUMERS", 1))))
        )
        await asyncio.Event().wait()  # Runs until loop.stop() is called

    finally:
        # In case shutdown() wasn't called via signal
        if not loop.is_closed():
            await db_manager.close()
            if connection:
                await connection.close()
        logger.info("Service has exited.")

if __name__ == "__main__":
    asyncio.run(main())
