# database.py
import motor.motor_asyncio

# MongoDB connection URI (adjust if needed)
MONGO_DETAILS = "mongodb://localhost:27017"

# Create a MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

# Access the MongoDB database
database = client["rules_db"]

# Access the collections in the database
rules_collection = database.get_collection("rules_collection")
