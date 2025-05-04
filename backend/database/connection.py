import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        username = quote_plus(os.getenv("MONGODB_USERNAME"))
        password = quote_plus(os.getenv("MONGODB_PASSWORD"))
        cluster = os.getenv("DB_CLUSTER")
        db_name = os.getenv("DB_NAME")

        uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print("Connected to MongoDB!")

    def close(self):
        self.client.close()
        print("MongoDB connection closed.")

db_instance = Database()