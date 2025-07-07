import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        db_name = os.getenv("DB_NAME", "UIBenchDB")

        uri = f"mongodb://localhost:27017"
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print("Connected to MongoDB!")

    def close(self):
        self.client.close()
        print("MongoDB connection closed.")

db_instance = Database()