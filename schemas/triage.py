from typing import Literal
from pydantic import BaseModel, Field


UrgencyLevel = Literal["emergency", "urgent", "routine", "non_medical"]


class SafetyFlag(BaseModel):
    category: str = Field(
        description="Category of the detected issue, e.g. cardiovascular, respiratory, neurological, hemorrhage, crisis"
    )
    flag: str = Field(description="Specific warning or red flag description")
    urgency: UrgencyLevel = Field(
        default="emergency",
        description="Urgency level associated with this flag",
    )


class TriageResult(BaseModel):
    is_medical: bool = Field(
        description="Whether the case involves medical symptoms or health advice"
    )
    is_emergency: bool = Field(
        description="True if life-threatening emergency symptoms are detected"
    )
    urgency_level: UrgencyLevel = Field(
        description="Overall urgency classification"
    )
    flags: list[SafetyFlag] = Field(
        default_factory=list,
        description="List of safety red flags triggered",
    )
    reasoning: str = Field(
        description="Clinical triage rationale explaining urgency level"
    )
    emergency_guidance: str | None = Field(
        default=None,
        description="Immediate emergency guidance if an emergency is detected (e.g. call 911 / 112, do not drive)",
    )

