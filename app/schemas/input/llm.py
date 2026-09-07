from pydantic import BaseModel, Field


class ItemVerdict(BaseModel):
    code: str = Field(description="Код пункту чекліста, рівно як у списку")
    passed: bool = Field(description="Чи виконав оператор цей пункт")
    quote: str | None = Field(
        default=None,
        description="Дослівна цитата з розмови. null якщо пункт не виконано",
    )
    confidence: float = Field(ge=0, le=1, description="Впевненість у висновку, 0..1")


class CallAnalysis(BaseModel):
    items: list[ItemVerdict]
