import asyncio
from app.consumer import start_consumer
from app.db import db_manager

async def main():
    """
    Entry point to start the consumer service and keep it running.
    Handles graceful shutdown on KeyboardInterrupt.
    """
    try:
        print("Starting text analysis service...")
        connection = await start_consumer()
        # Keep running until interrupted
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\nService stopped by user.")

    finally:
        # Cleanup resources
        await db_manager.close()
        if connection:
            await connection.close()
        print("Connections closed. Service stopped.")

if __name__ == "__main__":
    asyncio.run(main())
