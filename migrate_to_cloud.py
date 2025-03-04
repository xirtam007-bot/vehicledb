import sqlite3
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import certifi
import logging

load_dotenv()

# MongoDB Atlas connection string from environment variables
MONGO_URI = os.getenv('MONGO_URI')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_mongodb():
    """Migrate VIN records from SQLite to MongoDB Atlas"""
    try:
        # Connect to MongoDB Atlas with secure settings
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            retryWrites=True,
            w='majority',
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsCAFile=certifi.where()
        )
        db = client.vin_database
        vin_collection = db.vin_records
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect('vin_database.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get all records from SQLite
        sqlite_cursor.execute('SELECT * FROM vin_records')
        records = sqlite_cursor.fetchall()
        
        # Migrate each record
        for record in records:
            vin_doc = {
                'vin_value': record[1],
                'description': record[2],
                'scan_date': record[3],
                'migrated_at': datetime.utcnow()
            }
            vin_collection.update_one(
                {'vin_value': record[1]},
                {'$set': vin_doc},
                upsert=True
            )
            print(f"Migrated VIN: {record[1]}")
            
        print(f"\nSuccessfully migrated {len(records)} records to MongoDB")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    migrate_to_mongodb() 