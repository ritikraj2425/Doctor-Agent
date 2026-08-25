from typing import Any

from pydantic import BaseModel


class ResearchState(BaseModel):
    findings: list[dict[str, Any]]
    