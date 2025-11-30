from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from agent.scheduling_agent import SchedulingAgent

router = APIRouter()

# Single shared agent (keeps session memory)
agent = SchedulingAgent()

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or "default-session"

    response = await agent.handle_message(request.message, session_id)

    return ChatResponse(
        response=response,
        session_id=session_id
    )
