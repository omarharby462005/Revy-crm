import logging

from langchain_core.messages import HumanMessage, SystemMessage

from graph.prompts.direct_prompt import DIRECT_SYSTEM_PROMPT
from graph.state import AgentState
from llm.llm import get_gemini
from schemas.direct import DirectResponse
from services.messaging.client_service import ClientService
from utils.history_utils import get_chat_history
from utils.llm_utils import extract_token_usage
from utils.text_utils import detect_language_fallback


logger = logging.getLogger(__name__)


def direct_node(state: AgentState) -> dict:
    """Respond to greetings and general conversation."""
    user_message = state.get("user_message") or ""
    summary = state.get("summary") or ""
    usage = None

    try:
        client_service = ClientService(
            platform_id=state.get("platform_id"),
            page_id=state.get("page_id"),
            sender_id=state.get("sender_id"),
        )
        history, recent_history = get_chat_history(state, client_service)
        logger.info("[DIRECT] Processing message | history=%d", len(history))

        context = f"""Summary:
{summary or "None"}

Last Bot Message:
{state.get("last_bot_message") or "None"}

Recent Exchanges:
{recent_history or "None"}

"""

        messages = [
            SystemMessage(content=DIRECT_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        structured_llm = get_gemini().with_structured_output(
            DirectResponse,
            include_raw=True,
        )
        result = structured_llm.invoke(messages)

        raw = result.get("raw")
        if raw is not None:
            usage = extract_token_usage(raw)

        parsed = result.get("parsed")
        if parsed is None:
            raise ValueError("Gemini returned no parsed DirectResponse.")

        reply = parsed.reply
        summary = parsed.summary

    except Exception:
        logger.exception("[DIRECT] Failed to generate response")
        reply = detect_language_fallback(
            user_message,
            arabic="حصلت مشكلة مؤقتة وإحنا بنرد على رسالتك. ممكن تحاول تاني؟",
            default="A temporary issue occurred while processing your message. Please try again.",
        )

    return {
        "response": reply,
        "summary": summary,
        "last_bot_message": reply,
        "direct_usage": usage,
    }
