"""Export endpoint: GET /export/{summary_id} — download summary as PDF."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.core.limiter import limiter
from app.db.repositories.summary_repository import SummaryRepository
from app.services.export_service import generate_summary_pdf
from fastapi import Request

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/{summary_id}")
@limiter.limit("10/minute")
async def export_summary_pdf(
    request: Request,
    summary_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> Response:
    """Download a summary as a PDF file."""
    repo = SummaryRepository(db)
    record = await repo.get_by_id(summary_id, str(current_user["id"]))
    if not record:
        raise NotFoundError("Summary not found")

    pdf_bytes = generate_summary_pdf(record)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="summary-{summary_id}.pdf"',
        },
    )
