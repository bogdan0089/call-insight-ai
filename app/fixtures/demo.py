"""Seed demo calls: python -m app.fixtures.demo <slug> [--calls N] [--seed N] [--fresh]"""

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import async_session, engine
from app.fixtures.checklist import CHECKLIST
from app.fixtures.dialogues import DIALOGUES
from app.integrations.embeddings.client import build_embedder
from app.models.calls import Call, CallStatus
from app.models.checklist import ChecklistItem
from app.models.organizations import Organization
from app.models.scores import CallScore
from app.models.transcripts import Transcript, TranscriptSegment
from app.models.users import User, UserRole
from app.repositories.checklist import ChecklistRepository

SEGMENT_MS = 4000

TEAM = [
    ("Настя", "Коваль", UserRole.OPERATOR, 0.92),
    ("Артем", "Мельник", UserRole.OPERATOR, 0.74),
    ("Оксана", "Гриценко", UserRole.OPERATOR, 0.55),
    ("Ігор", "Бондар", UserRole.MANAGER, 0.85),
]

IN_PROGRESS = [CallStatus.QUEUED, CallStatus.TRANSCRIBING, CallStatus.ANALYZING]


async def find_organization(session, slug: str, create_as: str | None) -> Organization:
    result = await session.execute(select(Organization).where(Organization.slug == slug))
    organization = result.scalar_one_or_none()
    if organization is None and create_as:
        organization = Organization(name=create_as, slug=slug)
        session.add(organization)
        await session.flush()
        return organization
    if organization is None:
        existing = (await session.execute(select(Organization.slug))).scalars().all()
        available = ", ".join(existing) or "none"
        raise SystemExit(f"Organization '{slug}' not found. Available: {available}")
    return organization


async def ensure_checklist(session, organization: Organization) -> list[ChecklistItem]:
    result = await session.execute(
        select(ChecklistItem).where(ChecklistItem.organization_id == organization.id)
    )
    items = list(result.scalars().all())
    if items:
        return items

    await ChecklistRepository(session).add_many(organization.id, CHECKLIST)
    await session.flush()
    result = await session.execute(
        select(ChecklistItem).where(ChecklistItem.organization_id == organization.id)
    )
    return list(result.scalars().all())


async def ensure_team(session, organization: Organization) -> list[tuple[User, float]]:
    """Create demo operators and a manager if missing, without a usable password."""
    people: list[tuple[User, float]] = []
    manager: User | None = None

    for first, last, role, skill in TEAM:
        email = f"{first.lower()}.{organization.slug}@example.com"
        found = await session.execute(select(User).where(User.email == email))
        user = found.scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                hashed_password="",
                first_name=first,
                last_name=last,
                role=role,
                organization_id=organization.id,
                email_verified_at=datetime.now(UTC),
            )
            session.add(user)
            await session.flush()

        if role is UserRole.MANAGER:
            manager = user
        else:
            people.append((user, skill))

    if manager is not None:
        for user, _ in people:
            if user.manager_id is None:
                user.manager_id = manager.id

    await session.flush()
    return people


def pick_dialogue(skill: float, rng: random.Random) -> dict:
    """Pick a dialogue weighted by operator skill."""
    ranked = sorted(DIALOGUES, key=lambda d: len(d["expected_passed"]))
    weights = [(1 - skill) ** 2, 0.5, skill**2]
    return rng.choices(ranked, weights=weights[: len(ranked)], k=1)[0]


def pick_passed(items: list[ChecklistItem], skill: float, rng: random.Random) -> set[int]:
    """Decide which checklist items the operator passed."""
    dialogue = pick_dialogue(skill, rng)
    passed = {item.id for item in items if item.code in dialogue["expected_passed"]}

    for item in items:
        if item.id in passed and rng.random() > 0.5 + skill / 2:
            passed.discard(item.id)
        elif item.id not in passed and rng.random() < skill / 4:
            passed.add(item.id)

    return passed


def total_score(items: list[ChecklistItem], passed: set[int]) -> Decimal:
    weight = sum(item.weight for item in items)
    if not weight:
        return Decimal("0.00")
    earned = sum(item.weight for item in items if item.id in passed)
    return (Decimal(earned) / Decimal(weight) * 100).quantize(Decimal("0.01"))


async def build_call(
    session,
    organization: Organization,
    operator: User,
    skill: float,
    items: list[ChecklistItem],
    index: int,
    days: int,
    rng: random.Random,
    embedder,
) -> None:
    external_id = f"demo-{organization.slug}-{index}"
    exists = await session.execute(select(Call.id).where(Call.external_id == external_id))
    if exists.scalar_one_or_none() is not None:
        return

    created = datetime.now(UTC) - timedelta(
        days=rng.uniform(0, days), hours=rng.uniform(0, 12)
    )
    dialogue = rng.choice(DIALOGUES)
    segments = dialogue["segments"]

    roll = rng.random()
    if roll < 0.05:
        status = CallStatus.FAILED
    elif roll < 0.15:
        status = rng.choice(IN_PROGRESS)
    else:
        status = CallStatus.DONE

    call = Call(
        external_id=external_id,
        organization_id=organization.id,
        operator_id=operator.id,
        status=status,
        audio_path=f"demo/{external_id}.mp3",
        duration_sec=len(segments) * SEGMENT_MS // 1000,
        created_at=created,
        error="Transcription timed out" if status is CallStatus.FAILED else None,
    )
    session.add(call)
    await session.flush()

    if status is not CallStatus.DONE:
        return

    text = "\n".join(line for _, line in segments)
    transcript = Transcript(
        call_id=call.id,
        text=text,
        model="demo",
        embedding=await embedder.embed(text),
        embedding_model=embedder.model_name,
        created_at=created,
    )
    session.add(transcript)
    await session.flush()

    session.add_all(
        TranscriptSegment(
            transcript_id=transcript.id,
            idx=idx,
            speaker=speaker,
            start_ms=idx * SEGMENT_MS,
            end_ms=(idx + 1) * SEGMENT_MS,
            text=line,
        )
        for idx, (speaker, line) in enumerate(segments)
    )

    passed = pick_passed(items, skill, rng)
    operator_lines = [line for speaker, line in segments if speaker.value == "operator"]

    session.add_all(
        CallScore(
            call_id=call.id,
            checklist_item_id=item.id,
            passed=item.id in passed,
            quote=rng.choice(operator_lines) if operator_lines else None,
            quote_start_ms=rng.randrange(0, max(len(segments), 1) * SEGMENT_MS, SEGMENT_MS),
            confidence=Decimal(str(round(rng.uniform(0.62, 0.99), 2))),
            is_verified=rng.random() < 0.15,
            created_at=created,
        )
        for item in items
    )

    call.total_score = total_score(items, passed)


async def ensure_demo_login(session, organization: Organization) -> User:
    """Create the password-less demo owner used by the demo button."""
    found = await session.execute(select(User).where(User.email == settings.demo_email))
    user = found.scalar_one_or_none()
    if user is None:
        user = User(
            email=settings.demo_email,
            hashed_password="",
            first_name="Demo",
            last_name="Viewer",
            role=UserRole.OWNER,
            organization_id=organization.id,
            email_verified_at=datetime.now(UTC),
        )
        session.add(user)
    else:
        user.organization_id = organization.id
        user.role = UserRole.OWNER
        user.is_active = True
    await session.flush()
    return user


async def wipe(session, organization: Organization) -> int:
    """Delete the organization's demo calls."""
    result = await session.execute(
        select(Call).where(
            Call.organization_id == organization.id,
            Call.external_id.like(f"demo-{organization.slug}-%"),
        )
    )
    found = list(result.scalars().all())
    for call in found:
        await session.delete(call)
    await session.flush()
    return len(found)


async def fill(
    slug: str,
    calls: int,
    days: int,
    seed: int | None,
    fresh: bool,
    login: bool,
    create_as: str | None,
) -> None:
    rng = random.Random(seed)
    embedder = build_embedder()

    async with async_session() as session:
        organization = await find_organization(session, slug, create_as)
        if fresh:
            print(f"Removed demo calls: {await wipe(session, organization)}")
        items = await ensure_checklist(session, organization)
        if login:
            demo_user = await ensure_demo_login(session, organization)
            print(f"Demo login: {demo_user.email} (enable with DEMO_ENABLED=true)")
        team = await ensure_team(session, organization)
        if not team:
            raise SystemExit("The organization has no operators and none could be created")

        before = await session.execute(
            select(func.count()).select_from(Call).where(
                Call.organization_id == organization.id
            )
        )

        for index in range(calls):
            operator, skill = team[index % len(team)]
            await build_call(
                session, organization, operator, skill, items, index, days, rng, embedder
            )

        await session.commit()

        after = await session.execute(
            select(func.count()).select_from(Call).where(
                Call.organization_id == organization.id
            )
        )

    print(f"Organization: {organization.name} ({organization.slug})")
    print(f"Operators: {', '.join(user.full_name for user, _ in team)}")
    print(f"Checklist items: {len(items)}")
    print(f"Calls: {before.scalar_one()} -> {after.scalar_one()}")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for an organization")
    parser.add_argument("slug", help="organization slug, e.g. default")
    parser.add_argument("--calls", type=int, default=60)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducible data")
    parser.add_argument(
        "--fresh", action="store_true", help="delete previous demo calls first"
    )
    parser.add_argument(
        "--login", action="store_true", help="attach the demo button account to this organization"
    )
    parser.add_argument("--create", metavar="NAME", help="create the organization if it is missing")
    args = parser.parse_args()

    asyncio.run(
        fill(args.slug, args.calls, args.days, args.seed, args.fresh, args.login, args.create)
    )


if __name__ == "__main__":
    main()
