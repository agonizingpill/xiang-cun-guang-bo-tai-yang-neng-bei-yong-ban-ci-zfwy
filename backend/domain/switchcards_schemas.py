from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class IssueSwitch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    reserve: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    source: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    approved_wh: FiniteFloat


class Handover(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
