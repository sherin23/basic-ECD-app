import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load .env file for local development 
load_dotenv()

try:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin%40123@localhost:27017/foccai?authSource=admin")
    client = MongoClient(MONGO_URI)
    db = client.get_database("patient_ecd_db")

    users_collection = db["users"]
    patients_collection = db["patients"]
    medical_records_collection = db["medical_records"]
    ecd_collection = db["ecds"]
    audit_records_collection = db["audit_records"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None
    users_collection = None
    patients_collection = None
    medical_records_collection = None
    ecd_collection = None
    audit_records_collection = None

def init_db():
    if db is None:
        return
        
    try:
        # Create indexes if necessary
        users_collection.create_index("username", unique=True)
        
        # Seed default users
        if users_collection.count_documents({"username": "collector"}) == 0:
            users_collection.insert_one({
                "username": "collector",
                "password_hash": generate_password_hash("password"),
                "role": "collector"
            })
            print("Seeded 'collector' user.")
            
        if users_collection.count_documents({"username": "auditor"}) == 0:
            users_collection.insert_one({
                "username": "auditor",
                "password_hash": generate_password_hash("password"),
                "role": "auditor"
            })
            print("Seeded 'auditor' user.")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
    print("Database initialization complete.")
