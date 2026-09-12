from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class StatsQuery(BaseModel):
    operator_id: int | None = Field(default=None, ge=1)
    created_from: datetime | None = None
    created_to: datetime | None = None

    @model_validator(mode="after")
    def check_range(self) -> "StatsQuery":
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            raise ValueError("created_from must not be later than created_to")
        return self
