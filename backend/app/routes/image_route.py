import base64
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.database.auth import User, get_current_user
from app.database.chat_memory import save_message, get_conversation_context
from app.services.gemini_service import GeminiService
from app.services.cancel_service import clear_cancelled, is_cancelled

router = APIRouter()


@router.post("/image-chat")
async def image_chat(
    message: str = Form(...),
    session_id: str | None = Form(None),
    request_id: str | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    active_session_id = session_id or str(uuid.uuid4())
    conversation_context = get_conversation_context(active_session_id, user_id=user.id)
    image_bytes = await file.read()
    mime_type = file.content_type or "image/png"
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{mime_type};base64,{image_base64}"

    user_message = message
    save_message(active_session_id, "user", user_message, user_id=user.id)

    prompt = f"""
Previous Conversation in this chat:
{conversation_context or "No previous conversation in this chat."}

Current image request:
{user_message}

Instruction:
Use this chat's previous messages to understand the user's follow-up request, but answer based on the current image too.
"""

    response = GeminiService.analyze_image(
        prompt=prompt,
        image_data_url=image_data_url
    )

    if is_cancelled(request_id):
        clear_cancelled(request_id)
        return {
            "session_id": active_session_id,
            "agent": "cancelled",
            "response": "Generation stopped.",
            "cancelled": True
        }

    save_message(active_session_id, "assistant", response, user_id=user.id)
    clear_cancelled(request_id)

    return {
        "session_id": active_session_id,
        "agent": "image",
        "response": response
    }
