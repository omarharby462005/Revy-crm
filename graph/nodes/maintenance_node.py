import logging

from langchain_core.messages import HumanMessage, SystemMessage

from graph.prompts.maintenance_prompt import MAINTENANCE_SYSTEM_PROMPT
from graph.state import AgentState
from graph.tools.maintenance_tool import save_maintenance_tool
from llm.llm import get_gemini
from schemas.maintenance import MaintenanceResponse
from services.messaging.client_service import ClientService
from utils.history_utils import get_chat_history
from utils.text_utils import detect_language_fallback


logger = logging.getLogger(__name__)


def maintenance_node(state: AgentState) -> dict:
    """Collect and save an existing customer’s maintenance details."""
    user_message = state.get("user_message") or ""
    summary = state.get("summary") or ""

    try:
        client_service = ClientService(
            platform_id=state.get("platform_id"),
            page_id=state.get("page_id"),
            sender_id=state.get("sender_id"),
        )
        history, recent_history = get_chat_history(state, client_service)
        logger.info("[MAINTENANCE] Processing message | history=%d", len(history))

        context = f"""Summary:
{summary or "None"}

Last Bot Message:
{state.get("last_bot_message") or "None"}

Recent Exchanges:
{recent_history or "None"}

"""

        messages = [
            SystemMessage(content=MAINTENANCE_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        structured_llm = get_gemini().with_structured_output(
            MaintenanceResponse,
        )
        parsed = structured_llm.invoke(messages)
        if parsed is None:
            raise ValueError("Gemini returned no parsed MaintenanceResponse.")

        reply = parsed.reply
        if parsed.ready_to_save and parsed.project_name and parsed.phone_number:
            result = save_maintenance_tool.invoke({
                "project_name": parsed.project_name,
                "phone_number": parsed.phone_number,
            })
            if not result.success:
                raise RuntimeError("Maintenance record could not be saved.")

            reply = detect_language_fallback(
                user_message,
                arabic="تم تسجيل بيانات طلب الصيانة.",
                default="Your maintenance request details have been recorded.",
            )
            summary = f"{parsed.summary}\nMaintenance details recorded.".strip()
        else:
            summary = parsed.summary

    except Exception:
        logger.exception("[MAINTENANCE] Failed to generate response")
        reply = detect_language_fallback(
            user_message,
            arabic="حصلت مشكلة مؤقتة وإحنا بنرد على رسالتك. ممكن تحاول تاني؟",
            default="A temporary issue occurred while processing your message. Please try again.",
        )

    return {
        "response": reply,
        "summary": summary,
        "last_bot_message": reply,
    }
