import re

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia", "'": "", "ʼ": "",
}

SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(value: str, max_length: int) -> str:
    lowered = value.strip().lower()
    latin = "".join(TRANSLIT.get(char, char) for char in lowered)
    cleaned = SEPARATORS.sub("-", latin).strip("-")
    return cleaned[:max_length].strip("-")


def unique_slug(base: str, taken: set[str], max_length: int) -> str:
    if base and base not in taken:
        return base

    root = base or "org"
    for suffix in range(2, 1000):
        tail = f"-{suffix}"
        candidate = f"{root[: max_length - len(tail)]}{tail}"
        if candidate not in taken:
            return candidate

    raise ValueError("could not build a unique slug")
