from typing import Literal
from pydantic import BaseModel, Field


WarningSeverity = Literal["high", "moderate", "low"]
WarningType = Literal[
    "interaction",
    "duplicate_therapy",
    "allergy_risk",
    "prescription_risk",
    "precaution",
]


class MedicineItem(BaseModel):
    brand_name: str | None = Field(
        default=None,
        description="Trade or brand name mentioned, e.g. Tylenol, Crocin, Advil",
    )
    generic_name: str = Field(
        description="Active pharmaceutical ingredient / generic compound, e.g. Acetaminophen, Ibuprofen"
    )
    drug_class: str = Field(
        description="Pharmacological class, e.g. NSAID, Antipyretic, Analgesic"
    )
    prescription_required: bool = Field(
        description="True if prescription (Rx) only; False if Over-The-Counter (OTC)"
    )
    common_uses: str = Field(
        description="Standard indications for this medication"
    )
    common_contraindications: list[str] = Field(
        default_factory=list,
        description="Conditions where this medication is contraindicated or should be avoided",
    )


class MedicationWarning(BaseModel):
    severity: WarningSeverity = Field(
        description="Clinical risk level: high, moderate, or low"
    )
    warning_type: WarningType = Field(
        description="Classification of the medication safety warning"
    )
    message: str = Field(
        description="Clear explanation of the interaction, allergy risk, or precaution"
    )


class MedicationCheckResult(BaseModel):
    has_medication_mention: bool = Field(
        description="Whether medications were mentioned or relevant to the case"
    )
    medicines_identified: list[MedicineItem] = Field(
        default_factory=list,
        description="List of normalized generic medicines identified in the case",
    )
    warnings: list[MedicationWarning] = Field(
        default_factory=list,
        description="Safety warnings, potential drug interactions, or duplicate therapies",
    )
    pharmacist_note: str = Field(
        default="",
        description="General medication safety advice reminding user to consult a licensed pharmacist or physician",
    )

