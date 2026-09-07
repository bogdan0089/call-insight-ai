from pydantic import BaseModel


class ExampleVerdict(BaseModel):
    code: str
    passed: bool


class ScoredExample(BaseModel):
    call_id: int
    similarity: float
    excerpt: str
    verdicts: list[ExampleVerdict]
