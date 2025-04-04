from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from urllib.parse import quote_plus

class Database:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    async def connect(self):
        try:
            # Test the connection
            await self.client.admin.command('ping')
            print("Connected to MongoDB")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")

    async def close(self):
        self.client.close()
        print("MongoDB connection closed")

    def get_db(self):
        """Returns the database instance."""
        return self.db

# Database configuration
username = quote_plus("Milkeybear14")
password = quote_plus("Mickyastesfaye0965161472")
MONGO_URI = f"mongodb+srv://{username}:{password}@uibenchdb.hord20d.mongodb.net/?retryWrites=true&w=majority&appName=UIBenchDB"  # Replace with your MongoDB Atlas URI
DB_NAME = "UIBenchDB"

database = Database(MONGO_URI, DB_NAME)
