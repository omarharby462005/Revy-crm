"""Classify customer messages for Revy's LangGraph routes."""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from graph.prompts.intent_prompt import INTENT_SYSTEM_PROMPT
from graph.state import AgentState
from llm.llm import get_gemini
from schemas.intent import IntentResponse, IntentType
from services.messaging.client_service import ClientService
from utils.history_utils import get_chat_history
from utils.llm_utils import extract_token_usage


logger = logging.getLogger(__name__)


def intent_node(state: AgentState) -> dict[str, Any]:
    """Return the routing intent and Gemini token usage as state updates."""
    usage = None

    try:
        client_service = ClientService(
            platform_id=state.get("platform_id"),
            page_id=state.get("page_id"),
            sender_id=state.get("sender_id"),
        )
        _, formatted_history = get_chat_history(state, client_service)

        context = f"""Summary:
{state.get("summary") or "None"}

Last Bot Message:
{state.get("last_bot_message") or "None"}

Recent Exchanges:
{formatted_history or "None"}

"""

        messages = [
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

        classifier = get_gemini().with_structured_output(
            IntentResponse,
            include_raw=True,
        )
        result = classifier.invoke(messages)

        raw = result.get("raw")
        if raw is not None:
            usage = extract_token_usage(raw)

        parsed = result.get("parsed")
        if parsed is None:
            raise ValueError(" returned no parsed IntentResponse.")

        logger.info("[INTENT] Classified as %s", parsed.intent.value)
        return {"intent": parsed.intent, "intent_usage": usage}

    except Exception:
        logger.exception("[INTENT] Classification failed")
        return {"intent": IntentType.DIRECT, "intent_usage": usage}
