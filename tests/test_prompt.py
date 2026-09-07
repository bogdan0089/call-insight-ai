from app.integrations.llm.prompt import build_user_prompt
from app.models.checklist import ChecklistItem

TRANSCRIPT = "operator: алло\nclient: добрий день"


def make_items() -> list[ChecklistItem]:
    return [
        ChecklistItem(
            code="greeting",
            title="Привітався і назвав імʼя",
            description="Просте 'алло' не зараховується.",
        )
    ]


def test_prompt_has_checklist_and_transcript() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items())

    assert "ЧЕКЛІСТ:" in prompt
    assert "СТЕНОГРАМА:" in prompt
    assert prompt.index("ЧЕКЛІСТ:") < prompt.index("СТЕНОГРАМА:")


def test_prompt_carries_checklist_description() -> None:
    prompt = build_user_prompt(TRANSCRIPT, make_items())

    assert "greeting: Привітався і назвав імʼя" in prompt
    assert "Просте 'алло' не зараховується." in prompt
