from typing import Literal
from pydantic import BaseModel, Field


Likelihood = Literal["high", "moderate", "low"]


class PossibleCause(BaseModel):
    name: str = Field(
        description="Name of the condition or differential diagnosis"
    )
    likelihood: Likelihood = Field(
        description="Estimated probability tier: high, moderate, or low"
    )
    explanation: str = Field(
        description="Clinical reasoning connecting symptoms to this condition"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Key symptoms or findings supporting this diagnosis",
    )
    contradicting_factors: list[str] = Field(
        default_factory=list,
        description="Absent symptoms or factors that reduce certainty",
    )


class CareStep(BaseModel):
    title: str = Field(
        description="Short actionable title for conservative care or monitoring"
    )
    instructions: str = Field(
        description="Detailed safe guidance (e.g. hydration, rest, ice/elevation)"
    )


class DifferentialAnalysis(BaseModel):
    primary_impression: str = Field(
        description="Overall clinical summary of the presentation"
    )
    possible_causes: list[PossibleCause] = Field(
        description="Ranked list of potential diagnoses (differentials)"
    )
    care_steps: list[CareStep] = Field(
        default_factory=list,
        description="Safe, non-pharmacological supportive care steps",
    )
    doctor_questions: list[str] = Field(
        default_factory=list,
        description="Specific targeted questions the patient should bring to their doctor",
    )
    red_flag_warnings: list[str] = Field(
        default_factory=list,
        description="Warning symptoms that should prompt immediate in-person evaluation",
    )

