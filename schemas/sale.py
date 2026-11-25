from pydantic import BaseModel, Field


class SalesResponse(BaseModel):
    """Structured output for Revy's sales conversation node."""

    reply: str = Field(
        min_length=1,
        description="The customer-facing reply, written in the customer's language.",
    )

    summary: str = Field(
        description=(
            "An updated, concise summary of the conversation. Preserve relevant "
            "details from the existing summary and include only information "
            "supported by the conversation."
        ),
    )
