import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "marine_environment")


class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(MONGO_URI)
        print(f"Connected to MongoDB: {DB_NAME}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            print("Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        return cls.client[DB_NAME]
    
    @classmethod
    def get_collection(cls, collection_name: str = "samples"):
        """Get collection instance"""
        return cls.get_database()[collection_name]


# Helper function to get collection
def get_samples_collection():
    return Database.get_collection("samples")
