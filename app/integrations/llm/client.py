from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import anthropic

from app.core.config import settings
from app.integrations.llm.prompt import SYSTEM_PROMPT, build_user_prompt
from app.models.checklist import ChecklistItem
from app.schemas.input.llm import CallAnalysis, ItemVerdict
from app.schemas.input.rag import ScoredExample


@dataclass(frozen=True)
class AnalysisResult:
    analysis: CallAnalysis
    model: str
    input_tokens: int
    output_tokens: int
    raw: dict[str, Any]

    @property
    def cost_usd(self) -> float:
        return (
            self.input_tokens / 1_000_000 * settings.llm_input_price_per_mtok
            + self.output_tokens / 1_000_000 * settings.llm_output_price_per_mtok
        )


class LLMAnalyzer(Protocol):
    async def analyze(
        self,
        transcript: str,
        items: Sequence[ChecklistItem],
        examples: Sequence[ScoredExample] = (),
    ) -> AnalysisResult: ...


class AnthropicAnalyzer:
    def __init__(self, client: anthropic.AsyncAnthropic | None = None) -> None:
        self.client = client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    async def analyze(
        self,
        transcript: str,
        items: Sequence[ChecklistItem],
        examples: Sequence[ScoredExample] = (),
    ) -> AnalysisResult:
        prompt = build_user_prompt(transcript, items, examples)

        response = await self.client.messages.parse(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_format=CallAnalysis,
        )

        return AnalysisResult(
            analysis=response.parsed_output,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            raw=response.to_dict(),
        )


class FakeAnalyzer:
    def __init__(self, passed_codes: Sequence[str]) -> None:
        self.passed_codes = set(passed_codes)
        self.last_examples: list[ScoredExample] = []

    async def analyze(
        self,
        transcript: str,
        items: Sequence[ChecklistItem],
        examples: Sequence[ScoredExample] = (),
    ) -> AnalysisResult:
        self.last_examples = list(examples)

        verdicts = [
            ItemVerdict(
                code=item.code,
                passed=item.code in self.passed_codes,
                quote="фейкова цитата" if item.code in self.passed_codes else None,
                confidence=1.0,
            )
            for item in items
        ]

        return AnalysisResult(
            analysis=CallAnalysis(items=verdicts),
            model="fake",
            input_tokens=0,
            output_tokens=0,
            raw={"fake": True},
        )
