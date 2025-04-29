import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    _instance: Optional['Database'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        load_dotenv()
        
        try:
            username = quote_plus(os.getenv("MONGODB_USERNAME", ""))
            password = quote_plus(os.getenv("MONGODB_PASSWORD", ""))
            cluster = os.getenv("DB_CLUSTER", "")
            db_name = os.getenv("DB_NAME", "")
            
            if not all([username, password, cluster, db_name]):
                raise ValueError("Missing required database configuration")
            
            uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
            
            # Configure connection pool
            self.client = MongoClient(
                uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            logger.info("Successfully connected to MongoDB!")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"Server selection timeout: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {str(e)}")
            raise
        
        self._initialized = True
    
    def close(self):
        """Close the database connection."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("MongoDB connection closed.")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        try:
            return self.db[collection_name]
        except Exception as e:
            logger.error(f"Error accessing collection {collection_name}: {str(e)}")
            raise

# Create a singleton instance
db_instance = Database()
