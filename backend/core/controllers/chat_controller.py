"""Chat controller — orchestrates RAG context + OpenAI LLM call."""
from sqlite3 import Connection

from fastapi import HTTPException
from openai import OpenAI, AuthenticationError, RateLimitError

from commons.config import settings
from core.schemas import UserContext
from core.services.rag_service import build_wms_context, SYSTEM_PROMPT_TEMPLATE


ALLOWED_ROLES = {"ORG_ADMIN", "WAREHOUSE_MANAGER"}


def chat(conn: Connection, user: UserContext, message: str, history: list[dict]) -> dict:
    # ── Role guard ────────────────────────────────────────────────────────────
    if user.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Chat is only available to Admin and Manager roles.")

    # ── API key check ─────────────────────────────────────────────────────────
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
        raise HTTPException(
            status_code=503,
            detail="AI chatbot is not configured. Please add your OPENAI_API_KEY to the backend .env file.",
        )

    # ── Get this user's warehouse IDs ─────────────────────────────────────────
    wh_rows = conn.execute(
        "SELECT warehouse_id FROM user_warehouses WHERE user_id = ?", (user.id,)
    ).fetchall()
    warehouse_ids = [r["warehouse_id"] for r in wh_rows]

    # ── Build live context from DB ────────────────────────────────────────────
    context = build_wms_context(conn, user.role, warehouse_ids)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context, role=user.role.replace("_", " ").title())

    # ── Build message list for OpenAI ─────────────────────────────────────────
    messages = [{"role": "system", "content": system_prompt}]

    # Include last 10 turns of conversation history
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])[:2000]})

    messages.append({"role": "user", "content": message})

    # ── Call OpenAI ───────────────────────────────────────────────────────────
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            max_tokens=1024,
            temperature=0.2,  # Low temp = factual, consistent answers
        )
        reply = response.choices[0].message.content.strip()
        return {"reply": reply, "model": settings.chat_model}

    except AuthenticationError:
        raise HTTPException(status_code=503, detail="Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env.")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit reached. Please try again in a moment.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
