from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO
from app.logger import logger


class MongoDBManager:
    """
    Async MongoDB manager for upserting or deleting documents by 'id'.
    """

    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO['URI'])
        self.collection = self.client[MONGO['DB_NAME']][MONGO['COLLECTION']]
        logger.info("MongoDB client initialized")

    async def save_or_update(self, message: dict):
        """
        Upsert a document based on the 'id' field.

        Args:
            message (dict): Document data to save or update.
        """
        try:
            logger.debug(f"Upserting doc id={message['id']}")
            await self.collection.update_one(
                {'id': message['id']},
                {'$set': message},
                upsert=True
            )
            logger.info(f"Document upserted id={message['id']}")
        except Exception as e:
            logger.exception(f"Failed to upsert document id={message['id']}: {e}")

    async def delete(self, message_id: str):
        """
        Delete a document by 'id'.

        Args:
            message_id (str): Document id to delete.
        """
        try:
            logger.debug(f"Deleting document id={message_id}")
            result = await self.collection.delete_one({'id': message_id})
            if result.deleted_count:
                logger.info(f"Document deleted id={message_id}")
            else:
                logger.warning(f"No document found to delete id={message_id}")
        except Exception as e:
            logger.exception(f"Failed to delete document id={message_id}: {e}")


    async def close(self):
        """
        Close the MongoDB client connection.
        """
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.exception(f"Error closing MongoDB connection: {e}")

db_manager = MongoDBManager()

async def save_to_mongodb(message: dict):
    """
    Route to save or delete a message in MongoDB based on its action.

    Args:
        message (dict): Message dict containing 'action' key.
    """
    if message.get('action') == 'delete':
        await db_manager.delete(message['id'])
        return
    if message.get('action') == 'update':
        await db_manager.save_or_update(message)
    else:
        logger.error(f"Unknown action received: {message.get('action')}")
        raise ValueError(f"Unknown action: {message.get('action')}")

