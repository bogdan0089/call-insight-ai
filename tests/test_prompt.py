import pytest

from app.integrations.llm.client import FakeAnalyzer
from app.integrations.llm.prompt import build_user_prompt
from app.models.checklist import ChecklistItem
from app.schemas.input.rag import ExampleVerdict, ScoredExample

TRANSCRIPT = "operator: алло\nclient: добрий день"


def make_items() -> list[ChecklistItem]:
    return [
        ChecklistItem(
            code="greeting",
            title="Привітався і назвав імʼя",
            description="Просте 'алло' не зараховується.",
        )
    ]


def make_example() -> ScoredExample:
    return ScoredExample(
        call_id=7,
        similarity=0.91,
        excerpt="operator: добрий день, мене звати Олег",
        verdicts=[ExampleVerdict(code="greeting", passed=True)],
    )


def test_prompt_without_examples_has_no_examples_section() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items())

    assert "ЧЕКЛІСТ:" in prompt
    assert "СТЕНОГРАМА:" in prompt
    assert "ПРИКЛАДИ:" not in prompt


def test_prompt_carries_checklist_description() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items())

    assert "greeting: Привітався і назвав імʼя" in prompt
    assert "Просте 'алло' не зараховується." in prompt


def test_prompt_renders_examples_with_verdicts() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items(), [make_example()])

    assert "ПРИКЛАДИ:" in prompt
    assert "[приклад 1, схожість 0.91]" in prompt
    assert "greeting=так" in prompt


def test_examples_are_placed_before_transcript() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items(), [make_example()])

    assert prompt.index("ЧЕКЛІСТ:") < prompt.index("ПРИКЛАДИ:") < prompt.index("СТЕНОГРАМА:")


def test_failed_verdict_renders_as_no() -> None:
    example = make_example()
    example.verdicts[0].passed = False

    prompt = build_user_prompt(TRANSCRIPT, make_items(), [example])

    assert "greeting=ні" in prompt


@pytest.mark.asyncio
async def test_fake_analyzer_accepts_examples() -> None:
    analyzer = FakeAnalyzer(["greeting"])

    result = await analyzer.analyze(TRANSCRIPT, make_items(), [make_example()])

    assert analyzer.last_examples == [make_example()]
    assert result.analysis.items[0].passed is True
