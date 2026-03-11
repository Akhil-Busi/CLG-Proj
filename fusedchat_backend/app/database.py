# app/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import List

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
chat_collection = db["chats"]

# FIXED: Parameter names changed to match the call in main.py
async def save_chat(session_id: str, query: str, response: str, mode: str):
    """Saves a single chat message to the database."""
    document = {
        "session_id": session_id,
        "user_query": query,         # Changed from user_query
        "bot_response": response,    # Changed from bot_response
        "mode": mode,
    }
    await chat_collection.insert_one(document)

# FIXED: Added the 'limit' parameter to the function definition
async def get_history(session_id: str, limit: int = 20) -> List[dict]:
    """Retrieves chat history for a given session ID."""
    cursor = chat_collection.find(
        {"session_id": session_id}
    ).sort("_id", -1).limit(limit)  # Sort by most recent and limit
    
    # The to_list method already handles async iteration
    history = await cursor.to_list(length=limit)
    # Reverse the list so the oldest messages are first
    return history[::-1]