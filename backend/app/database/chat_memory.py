from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func, or_
from app.database.db import Base, engine, SessionLocal


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def ensure_chat_schema():
    with engine.connect() as connection:
        columns = connection.exec_driver_sql("PRAGMA table_info(chat_messages)").fetchall()
        column_names = [column[1] for column in columns]
        if "user_id" not in column_names:
            connection.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN user_id INTEGER")
            connection.commit()


ensure_chat_schema()


def save_message(session_id: str, role: str, content: str, user_id: int | None = None):
    db = SessionLocal()

    message = ChatMessage(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content
    )

    db.add(message)
    db.commit()
    db.close()


def get_messages(session_id: str, user_id: int | None = None):
    db = SessionLocal()

    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)

    if user_id is not None:
        query = query.filter(or_(ChatMessage.user_id == user_id, ChatMessage.user_id.is_(None)))

    messages = query.order_by(ChatMessage.created_at.asc()).all()

    db.close()

    return [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": str(msg.created_at)
        }
        for msg in messages
    ]


def get_all_sessions(user_id: int | None = None):
    db = SessionLocal()

    query = db.query(
        ChatMessage.session_id,
        func.max(ChatMessage.created_at).label("last_message_at")
    )

    if user_id is not None:
        query = query.filter(or_(ChatMessage.user_id == user_id, ChatMessage.user_id.is_(None)))

    latest_messages = (
        query.group_by(ChatMessage.session_id)
        .order_by(func.max(ChatMessage.created_at).desc())
        .all()
    )

    sessions = []
    for session_id, last_message_at in latest_messages:
        first_query = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        )

        if user_id is not None:
            first_query = first_query.filter(or_(ChatMessage.user_id == user_id, ChatMessage.user_id.is_(None)))

        first_user_message = first_query.order_by(ChatMessage.created_at.asc()).first()

        title = first_user_message.content if first_user_message else "New chat"
        title = " ".join(title.split())
        if len(title) > 44:
            title = title[:41] + "..."

        sessions.append({
            "id": session_id,
            "title": title,
            "last_message_at": str(last_message_at)
        })

    db.close()

    return sessions


def delete_session(session_id: str, user_id: int | None = None):
    db = SessionLocal()

    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)

    if user_id is not None:
        query = query.filter(or_(ChatMessage.user_id == user_id, ChatMessage.user_id.is_(None)))

    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    db.close()

    return deleted_count


def get_conversation_context(
    session_id: str,
    user_id: int | None = None,
    limit: int = 12,
    max_chars: int = 6000
):
    messages = get_messages(session_id, user_id=user_id)
    recent_messages = messages[-limit:]
    lines = []

    for message in recent_messages:
        role = "User" if message["role"] == "user" else "Assistant"
        content = " ".join(str(message["content"]).split())
        if content:
            lines.append(f"{role}: {content}")

    context = "\n".join(lines)

    if len(context) > max_chars:
        context = context[-max_chars:]

    return context
