"""Extract plain text from uploaded case files (txt, md, pdf)."""

from io import BytesIO

from fastapi import HTTPException, UploadFile


async def extract_uploaded_file_text(upload: UploadFile) -> str:
    raw = await upload.read()
    if not raw:
        return ""

    name = (upload.filename or "upload").lower()

    if name.endswith(".txt") or name.endswith(".md"):
        return raw.decode("utf-8", errors="replace").strip()

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(raw))
            parts: list[str] = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
            return "\n".join(parts).strip()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=400,
                detail=f"Could not read PDF: {exc}",
            ) from exc

    raise HTTPException(
        status_code=415,
        detail="Unsupported file type. Use .txt, .md, or .pdf.",
    )


def merge_case_text_and_file(case_text: str, file_text: str) -> str:
    """Append extracted file content after case text when both are present."""
    parts: list[str] = []
    ct = (case_text or "").strip()
    ft = (file_text or "").strip()
    if ct:
        parts.append(ct)
    if ft:
        parts.append("--- Contents from uploaded file ---\n" + ft)
    return "\n\n".join(parts)
