from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import AgentStep, Case


async def fetch_cases_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    title_query: str | None,
) -> list[Case]:
    stmt = select(Case).where(Case.user_id == user_id).order_by(Case.created_at.desc())
    q = (title_query or "").strip()
    if q:
        stmt = stmt.where(Case.title.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def fetch_case_detail_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    case_id: str,
) -> Case | None:
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id, Case.user_id == user_id)
        .options(selectinload(Case.steps))
    )
    return result.scalar_one_or_none()


async def delete_case_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    case_id: str,
) -> bool:
    exists = await db.execute(select(Case.id).where(Case.id == case_id, Case.user_id == user_id))
    if exists.scalar_one_or_none() is None:
        return False
    await db.execute(delete(AgentStep).where(AgentStep.case_id == case_id))
    await db.execute(delete(Case).where(Case.id == case_id, Case.user_id == user_id))
    await db.commit()
    return True
