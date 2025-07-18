from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO

class MongoDBManager:
    """
    Async MongoDB manager for upserting or deleting documents by 'id'.
    """

    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO['URI'])
        self.collection = self.client[MONGO['DB_NAME']][MONGO['COLLECTION']]

    async def save_or_update(self, message: dict):
        """
        Upsert a document based on the 'id' field.

        Args:
            message (dict): Document data to save or update.
        """
        await self.collection.update_one(
            {'id': message['id']},
            {'$set': message},
            upsert=True
        )

    async def delete(self, message_id: str):
        """
        Delete a document by 'id'.

        Args:
            message_id (str): Document id to delete.
        """
        await self.collection.delete_one({'id': message_id})

    async def close(self):
        """
        Close the MongoDB client connection.
        """
        self.client.close()

db_manager = MongoDBManager()

async def save_to_mongodb(message: dict):
    """
    Route to save or delete a message in MongoDB based on its action.

    Args:
        message (dict): Message dict containing 'action' key.
    """
    if message.get('action') == 'delete':
        await db_manager.delete(message['id'])
    else:
        await db_manager.save_or_update(message)
