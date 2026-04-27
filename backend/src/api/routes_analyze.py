from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.orchestrator import run_pipeline
from src.api.dependencies import get_current_user
from src.database.session import get_db
from src.schemas.api_schemas import AnalyzePipelineInput, CurrentUser
from src.services.case_file_text import extract_uploaded_file_text, merge_case_text_and_file

router = APIRouter()


def _normalize_title(title: str) -> str:
    t = (title or "").strip()
    if not t:
        raise HTTPException(status_code=422, detail="title is required")
    return t[:255]


@router.post("/analyze")
async def analyze(
    title: str = Form(...),
    case_text: str = Form(""),
    case_file: UploadFile | None = File(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    title_clean = _normalize_title(title)
    case_text_stripped = (case_text or "").strip()

    file_excerpt = ""
    if case_file is not None and (case_file.filename or "").strip():
        file_excerpt = await extract_uploaded_file_text(case_file)

    merged = merge_case_text_and_file(case_text_stripped, file_excerpt)
    if not merged.strip():
        raise HTTPException(
            status_code=422,
            detail="Provide case text and/or a non-empty supported file (.txt, .md, .pdf).",
        )

    try:
        payload = AnalyzePipelineInput(title=title_clean, raw_case_text=merged)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return StreamingResponse(
        run_pipeline(payload, current_user.user_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
