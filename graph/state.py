from typing import Any, Optional, TypedDict

from schemas.intent import IntentType


class AgentState(TypedDict, total=False):

    # =========================
    # Platform
    # =========================
    page_id: Optional[str]
    sender_id: Optional[str]
    platform_id: Optional[int]
    platform_name: Optional[str]

    # =========================
    # Conversation
    # =========================
    user_message: str
    response: Optional[str]
    chat_history: Optional[list[dict[str, Any]]]
    summary: Optional[str]
    last_bot_message: Optional[str]

    # =========================
    # Routing
    # =========================
    intent: Optional[IntentType]

    # =========================
    # Booking
    # =========================
    booking_data: Optional[dict[str, Any]]
    booking_reference: Optional[str]
    booking_saved: Optional[bool]

    # =========================
    # Usage
    # =========================
    intent_usage: Optional[dict[str, Any]]
    booking_usage: Optional[dict[str, Any]]
    sales_usage: Optional[dict[str, Any]]
    direct_usage: Optional[dict[str, Any]]