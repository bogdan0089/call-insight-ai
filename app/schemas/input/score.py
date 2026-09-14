from pydantic import BaseModel


class ScoreVerifyRequest(BaseModel):
    is_verified: bool = True
