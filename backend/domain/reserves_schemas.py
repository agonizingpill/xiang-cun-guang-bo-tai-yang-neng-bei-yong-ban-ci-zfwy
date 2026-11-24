from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class ForecastWh(BaseModel):
    model_config = ConfigDict(extra="forbid")
    airslot: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    meter: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    clear: bool


class SaveReserve(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
