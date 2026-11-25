from typing import Literal

from pydantic import BaseModel, Field


class BookingReply(BaseModel):
    """Continue the conversation when a sales booking is not ready to submit."""

    reply: str = Field(
        ...,
        min_length=1,
        description=(
            "Reply naturally in the customer's language, using Egyptian Arabic "
            "for Arabic conversations. Ask for one missing detail at a time. "
            "Never invent booking details or claim a booking was confirmed."
        ),
    )
    summary: str = Field(
        ...,
        description=(
            "Update the cumulative conversation summary. Preserve known booking "
            "details and any previously reported booking outcome. Apply explicit "
            "customer corrections and leave missing details unspecified."
        ),
    )


class BookingRequest(BaseModel):
    """Submit a clear request to schedule a sales call or meeting."""

    phone_number: str = Field(
        ...,
        description="The customer's phone number in international format with a leading +.",
    )
    start_at: str = Field(
        ...,
        description="The customer's proposed start date and time in ISO 8601 format with a UTC offset.",
    )
    type: Literal["call", "meeting"] = Field(
        ...,
        description="The booking type the customer requested.",
    )
    description: str | None = Field(
        default=None,
        description="Optional sales discussion details supplied by the customer.",
    )
