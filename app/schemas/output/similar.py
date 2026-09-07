from pydantic import BaseModel


class SimilarCall(BaseModel):
    call_id: int
    similarity: float
    excerpt: str
