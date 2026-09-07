from collections.abc import Sequence

from app.models.checklist import ChecklistItem
from app.schemas.input.rag import ScoredExample

SYSTEM_PROMPT = """Ти — контролер якості телефонних розмов відділу продажів.

Тобі дають стенограму розмови і чекліст. Для кожного пункту чекліста визнач,
чи виконав його ОПЕРАТОР, а не клієнт.

Правила:
- Суди тільки за тим, що є в стенограмі. Не додумуй і не припускай.
- quote — дослівний фрагмент репліки оператора, скопійований без змін.
- Якщо пункт не виконано, quote має бути null.
- confidence знижуй, коли формулювання неоднозначне.
- Поверни рівно стільки елементів, скільки пунктів у чеклісті, з тими самими code.
- Блок ПРИКЛАДИ, якщо він є, — це схожі розмови з оцінками, які підтвердила людина.
  Тримай ту саму планку строгості, але оцінюй поточну розмову тільки за її змістом."""


def build_user_prompt(
    transcript: str,
    items: Sequence[ChecklistItem],
    examples: Sequence[ScoredExample] = (),
) -> str:
    checklist = "\n".join(
        f"- {item.code}: {item.title}. {item.description}" for item in items
    )

    parts = [f"ЧЕКЛІСТ:\n{checklist}"]
    if examples:
        parts.append(f"ПРИКЛАДИ:\n{_render_examples(examples)}")
    parts.append(f"СТЕНОГРАМА:\n{transcript}")

    return "\n\n".join(parts)


def _render_examples(examples: Sequence[ScoredExample]) -> str:
    blocks = []
    for number, example in enumerate(examples, start=1):
        verdicts = ", ".join(
            f"{verdict.code}={'так' if verdict.passed else 'ні'}"
            for verdict in example.verdicts
        )
        blocks.append(
            f"[приклад {number}, схожість {example.similarity}]\n"
            f"ФРАГМЕНТ: {example.excerpt}\n"
            f"ОЦІНКИ: {verdicts}"
        )
    return "\n\n".join(blocks)
