from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database.session import get_db
from src.schemas.api_schemas import CurrentUser, HistoryDetail, HistoryItem
from src.serializers import cases as cases_serializer

router = APIRouter()


@router.get("", response_model=list[HistoryItem])
async def list_history(
    q: str | None = Query(
        None,
        description="Case-insensitive substring match on case title only.",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cases_serializer.fetch_cases_for_user(
        db,
        user_id=current_user.user_id,
        title_query=q,
    )


@router.get("/{analysis_id}", response_model=HistoryDetail)
async def get_history_item(
    analysis_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await cases_serializer.fetch_case_detail_for_user(
        db,
        user_id=current_user.user_id,
        case_id=analysis_id,
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return case


@router.delete("/{analysis_id}", status_code=204)
async def delete_history_item(
    analysis_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted = await cases_serializer.delete_case_for_user(
        db,
        user_id=current_user.user_id,
        case_id=analysis_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return Response(status_code=204)
