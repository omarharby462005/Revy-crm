import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_chat_history(
    state,
    client_service,
    limit: int = 6,
) -> tuple[list[dict[str, Any]], str]:
    """Get chat history from state or client service."""

    history = state.get("chat_history")

    if history is None:
        try:
            history = client_service.get_chat_history(limit=limit)

        except Exception as exc:
            logger.warning("Failed to load chat history: %s", exc)
            history = []

    history = history or []

    normalized_history = [
        {
            "lead": turn.get("lead", turn.get("user", "")),
            "bot": turn.get("bot", ""),
            "timestamp": turn.get("timestamp", "")
        }
        for turn in history
    ]

    return normalized_history, format_chat_history(normalized_history)


def format_chat_history(
    history_exchanges: list[dict[str, Any]],
) -> str:
    """Convert chat history into JSON for the LLM."""

    return json.dumps(
        history_exchanges,
        ensure_ascii=False,
        indent=2
    )