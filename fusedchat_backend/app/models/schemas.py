from pydantic import BaseModel


class ChatRequest(BaseModel):
	session_id: str
	query: str
	is_document_mode: bool = False
