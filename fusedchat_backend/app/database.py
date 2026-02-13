from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
chat_collection = db["chats"]


async def save_chat(session_id: str, user_query: str, bot_response: str, mode: str):
	document = {
		"session_id": session_id,
		"user_query": user_query,
		"bot_response": bot_response,
		"mode": mode,
	}
	await chat_collection.insert_one(document)


async def get_history(session_id: str):
	cursor = chat_collection.find({"session_id": session_id}).limit(20)
	return await cursor.to_list(length=20)
