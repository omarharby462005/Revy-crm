"""Revy sales booking conversation node."""

import json
import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from graph.prompts.booking_prompt import BOOKING_SYSTEM_PROMPT
from graph.state import AgentState
from graph.tools.booking_tool import create_booking
from llm.llm import get_gemini
from schemas.booking import BookingReply, BookingRequest
from utils.llm_utils import extract_token_usage
from utils.text_utils import detect_language_fallback
from utils.timeutils import now_local


logger = logging.getLogger(__name__)

def booking_node(state: AgentState) -> dict:
    user_message = state["user_message"]
    summary = state.get("summary") or ""
    current_time = now_local().strftime("%Y-%m-%d %H:%M:%S %Z")
    usage = {}

    def localized(arabic: str, english: str) -> str:
        return detect_language_fallback(user_message, arabic=arabic, default=english)

    def finish(reply: str, **updates) -> dict:
        return {
            "response": reply,
            "summary": summary,
            "last_bot_message": reply,
            "booking_usage": usage,
            **updates,
        }

    fallback = localized(
        "حصلت مشكلة مؤقتة أثناء معالجة طلب الحجز.",
        "A temporary issue occurred while processing your booking request.",
    )
    context = {
        "current_time": current_time,
        "timezone": "Africa/Cairo",
        "recent_history": (state.get("chat_history") or [])[-12:],
        "summary": summary,
        "last_bot_message": state.get("last_bot_message"),
    }

    try:
        llm = get_gemini().bind_tools(
            [BookingRequest, BookingReply], tool_choice="any"
        )
        response = llm.invoke([
            SystemMessage(content=BOOKING_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(
                {"context": context, "customer_message": user_message},
                ensure_ascii=False,
            )),
        ])
        usage = extract_token_usage(response) or {}

        if len(response.tool_calls) != 1:
            return finish(fallback)

        call = response.tool_calls[0]
        if call["name"] == "BookingReply":
            conversation = BookingReply(**call["args"])
            return finish(conversation.reply, summary=conversation.summary)

        if call["name"] != "BookingRequest":
            return finish(fallback)

        booking = BookingRequest(**call["args"])

    except ValidationError:
        return finish(fallback)
    except Exception:
        logger.exception("[BOOKING] Could not process the conversation")
        return finish(fallback)

    booking_data = booking.model_dump()
    result = create_booking(
        **booking_data,
        endpoint=os.environ.get("REVY_CRM_BOOKING_ENDPOINT", ""),
        token=os.environ.get("REVY_CRM_BOOKING_TOKEN", ""),
    )

    outcome = result["outcome"]
    if outcome == "scheduled":
        reference = str(result["id"])
        return finish(
            localized(
                f"تم تأكيد موعدك مع فريق المبيعات. رقم الحجز {reference}.",
                f"Your appointment with our sales team is confirmed. Booking ID {reference}.",
            ),
            summary=f"{summary}\nCRM confirmed booking {reference} at {booking.start_at}.".strip(),
            booking_saved=True,
            booking_reference=reference,
            booking_data=booking_data,
        )

    if outcome == "unknown":
        return finish(
            localized(
                "مقدرتش أتحقق من تأكيد الموعد. ممكن الطلب يكون وصل بالفعل.",
                "I couldn't verify the appointment. Your request may already have reached us.",
            ),
            summary=f"{summary}\nCRM booking outcome is unknown for {booking.type} at {booking.start_at}. Avoid resubmitting the same request.".strip(),
            booking_saved=None,
            booking_reference=None,
            booking_data=booking_data,
        )

    if outcome == "invalid_input":
        prompts = {
            "phone_number": ("ممكن تبعت رقم تليفونك مع كود الدولة؟", "Could you share your phone number with its country code?"),
            "start_at": ("ممكن تحدد يوم وساعة الموعد؟", "Could you specify the appointment day and time?"),
            "type": ("تفضّل مكالمة ولا اجتماع؟", "Would you prefer a call or a meeting?"),
        }
        reply = localized(*prompts[result["field"]])
    elif outcome == "rejected":
        reply = localized(
            "الـCRM ما قدرش يقبل طلب الحجز بالبيانات دي.",
            "The booking system couldn't accept this request.",
        )
    else:
        reply = fallback

    return finish(
        reply,
        booking_saved=False,
        booking_reference=None,
        booking_data=booking_data,
    )
