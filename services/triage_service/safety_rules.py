import re
from schemas.triage import SafetyFlag


class SafetyRuleEngine:
    """
    Deterministic rule engine that scans text for critical medical
    red flags warranting immediate emergency escalation.
    
    This runs BEFORE any LLM call to guarantee that life-threatening
    patterns are never missed due to model hallucination or latency.
    """

    RED_FLAG_PATTERNS = [
        # Cardiovascular / Chest Pain
        (
            r"\b(crushing|radiating|pressure|squeezing)\s+chest\s+pain\b|"
            r"\bchest\s+pain\s+(radiating|spreading)\s+to\s+(left\s+arm|jaw|neck|back)\b|"
            r"\bheart\s+attack\b|\bcardiac\s+arrest\b",
            "cardiovascular",
            "Potential acute coronary syndrome (heart attack) red flag.",
        ),
        # Respiratory Distress
        (
            r"\b(can'?t|cannot|unable\s+to)\s+breathe\b|"
            r"\bsevere\s+(shortness\s+of\s+breath|dyspnea)\b|"
            r"\bstridor\b|\bturning\s+blue\b|\bcyanosis\b|"
            r"\bgasping\s+for\s+air\b",
            "respiratory",
            "Acute respiratory compromise detected.",
        ),
        # Stroke / Neurological (FAST criteria)
        (
            r"\b(facial\s+droop|face\s+drooping)\b|"
            r"\bslurred\s+speech\b|"
            r"\bsudden\s+(weakness|numbness)\s+(on\s+one\s+side|in\s+(one\s+)?arm|in\s+(one\s+)?leg)\b|"
            r"\bthunderclap\s+headache\b|"
            r"\bworst\s+headache\s+of\s+(my\s+)?life\b|"
            r"\bloss\s+of\s+consciousness\b|\bunresponsive\b",
            "neurological",
            "Potential acute stroke or intracranial hemorrhage (FAST emergency).",
        ),
        # Severe Anaphylaxis / Allergic Reaction
        (
            r"\b(throat\s+(is\s+)?closing|throat\s+swelling|tongue\s+swelling)\b|"
            r"\banaphylaxis\b|"
            r"\bswelling\s+(in|of)\s+throat\b",
            "anaphylaxis",
            "Potential acute anaphylaxis / severe airway obstruction.",
        ),
        # Severe Bleeding / Hemorrhage
        (
            r"\bcoughing\s+(up\s+)?blood\b|\bvomiting\s+blood\b|"
            r"\bhematemesis\b|\bhemoptysis\b|"
            r"\buncontrolled\s+bleeding\b|\bmassive\s+blood\s+loss\b",
            "hemorrhage",
            "Active severe internal or external hemorrhage detected.",
        ),
        # Suicidal Ideation / Self Harm Crisis
        (
            r"\b(want\s+to\s+die|commit\s+suicide|kill\s+myself|"
            r"end\s+my\s+life|suicidal\s+thoughts)\b",
            "mental_health_crisis",
            "Immediate crisis / self-harm signal detected.",
        ),
    ]

    @classmethod
    def scan_for_red_flags(cls, text: str) -> list[SafetyFlag]:
        """Scan input text against all red-flag patterns and return matches."""
        if not text:
            return []

        flags: list[SafetyFlag] = []
        lowered = text.lower()

        for pattern, category, description in cls.RED_FLAG_PATTERNS:
            if re.search(pattern, lowered):
                flags.append(
                    SafetyFlag(
                        category=category,
                        flag=description,
                        urgency="emergency",
                    )
                )

        return flags

