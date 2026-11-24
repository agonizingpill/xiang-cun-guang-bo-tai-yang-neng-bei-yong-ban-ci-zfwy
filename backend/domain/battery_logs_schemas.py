from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class LogCharge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    meter: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    hour: int
    load_wh: FiniteFloat
    clear: bool


class ApproveMeter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
