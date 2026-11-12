import re

from schemas.safety import (
    SafetyReview,
    DoctorAgentFinalResponse,
    STANDARD_MEDICAL_DISCLAIMER,
)


class SafetyGuard:
    """
    Deterministic post-generation auditor that:
    - Strips dangerous dosage recommendations
    - Softens absolute diagnostic assertions into probabilistic language
    - Ensures mandatory medical and regulatory disclaimers are appended
    - Assembles the final structured DoctorAgentFinalResponse
    """

    DOSAGE_PATTERN = re.compile(
        r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|tablets?|pills?|capsules?)"
        r"\s+(every|per|twice|three\s+times|daily|once)\b",
        re.IGNORECASE,
    )

    CERTAINTY_PATTERNS = [
        (
            re.compile(r"\byou\s+definitely\s+have\b", re.IGNORECASE),
            "your symptoms may be consistent with",
        ),
        (
            re.compile(r"\bwe\s+diagnose\s+you\s+with\b", re.IGNORECASE),
            "potential conditions to discuss with your doctor include",
        ),
        (
            re.compile(r"\byou\s+have\s+been\s+diagnosed\s+with\b", re.IGNORECASE),
            "a possible differential consideration is",
        ),
        (
            re.compile(r"\byou\s+have\b", re.IGNORECASE),
            "you may have",
        ),
    ]

    def audit_response(
        self,
        summary_text: str,
        is_emergency: bool = False,
        urgency_level: str = "routine",
        differential: dict | None = None,
        medication_check: dict | None = None,
        triage: dict | None = None,
    ) -> tuple[DoctorAgentFinalResponse, SafetyReview]:

        issues_found: list[str] = []
        modifications: list[str] = []
        has_dosage_risk = False

        cleaned_summary = summary_text

        # 1. Check for specific dosage recommendations
        if self.DOSAGE_PATTERN.search(cleaned_summary):
            has_dosage_risk = True
            issues_found.append(
                "Unauthorized specific medication dosage instructions detected."
            )
            cleaned_summary = self.DOSAGE_PATTERN.sub(
                "[dosage omitted — consult your prescribing doctor or pharmacist]",
                cleaned_summary,
            )
            modifications.append(
                "Sanitized specific drug dosages to prevent unprescribed dosing."
            )

        # 2. Check for over-certain diagnostic claims
        for pattern, replacement in self.CERTAINTY_PATTERNS:
            if pattern.search(cleaned_summary):
                issues_found.append("Over-certain diagnostic phrasing detected.")
                cleaned_summary = pattern.sub(replacement, cleaned_summary)
                modifications.append(
                    f"Softened diagnostic certainty to '{replacement}'."
                )

        # 3. Assemble structured differential details
        diff_data = differential or {}
        possible_causes = diff_data.get("possible_causes", [])
        care_steps = diff_data.get("care_steps", [])
        doctor_questions = diff_data.get("doctor_questions", [])

        # 4. Assemble medication details
        med_data = medication_check or {}
        medicines = med_data.get("medicines_identified", [])
        warnings = med_data.get("warnings", [])

        # 5. Inject emergency flags into warnings if present
        if triage and triage.get("flags"):
            for flag in triage["flags"]:
                warnings.insert(
                    0,
                    {
                        "severity": flag.get("urgency", "emergency"),
                        "warning_type": "precaution",
                        "message": (
                            f"[{flag.get('category', 'general').upper()}] "
                            f"{flag.get('flag', '')}"
                        ),
                    },
                )

        final_response = DoctorAgentFinalResponse(
            is_medical=True,
            is_emergency=is_emergency,
            urgency_level=urgency_level,
            summary=cleaned_summary,
            possible_causes=possible_causes,
            care_steps=care_steps,
            medicines=medicines,
            warnings=warnings,
            doctor_questions=doctor_questions,
            disclaimer=STANDARD_MEDICAL_DISCLAIMER,
        )

        review = SafetyReview(
            is_safe=not has_dosage_risk,
            issues_found=issues_found,
            contains_prohibited_dosages=has_dosage_risk,
            modifications_made=modifications,
        )

        return final_response, review

