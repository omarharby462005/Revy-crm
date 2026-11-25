from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    BOOKING = "booking"
    SALES = "sales"
    DIRECT = "direct"
    MAINTENANCE = "maintenance"


class IntentResponse(BaseModel):
    intent: IntentType = Field(
        ...,
        description=(
            "Classify the current message using the conversation context. "
            "Use booking for requests to schedule a sales call or meeting "
            "and for replies that provide details for an ongoing booking. "
            "Use sales for questions about Revy's projects, services, or features. "
            "Use maintenance for maintenance or repair requests. "
            "Use direct for greetings and general conversation."
        ),
    )