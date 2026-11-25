from pydantic import BaseModel, Field


class MaintenanceResponse(BaseModel):
    reply: str = Field(
        min_length=1,
        description="Reply in the customer's language. Ask for one missing detail at a time.",
    )
    summary: str = Field(description="Updated concise conversation summary.")
    project_name: str | None = Field(
        default=None,
        description="The project name the customer supplied for the current request.",
    )
    phone_number: str | None = Field(
        default=None,
        description="The phone number the customer supplied for the current request.",
    )
    ready_to_save: bool = Field(
        description=(
            "True only when the current request is new or still awaiting registration "
            "and the customer has supplied both fields. False for follow-ups on a "
            "request already recorded and for incomplete requests."
        ),
    )
