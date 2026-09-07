from collections.abc import Sequence

from app.models.checklist import ChecklistItem

SYSTEM_PROMPT = """Ти — контролер якості телефонних розмов відділу продажів.

Тобі дають стенограму розмови і чекліст. Для кожного пункту чекліста визнач,
чи виконав його ОПЕРАТОР, а не клієнт.

Правила:
- Суди тільки за тим, що є в стенограмі. Не додумуй і не припускай.
- quote — дослівний фрагмент репліки оператора, скопійований без змін.
- Якщо пункт не виконано, quote має бути null.
- confidence знижуй, коли формулювання неоднозначне.
- Поверни рівно стільки елементів, скільки пунктів у чеклісті, з тими самими code."""


def build_user_prompt(transcript: str, items: Sequence[ChecklistItem]) -> str:
    checklist = "\n".join(
        f"- {item.code}: {item.title}. {item.description}" for item in items
    )
    return f"ЧЕКЛІСТ:\n{checklist}\n\nСТЕНОГРАМА:\n{transcript}"
