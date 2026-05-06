"""Export service — generate a PDF report from a summary record."""

from __future__ import annotations

import io
from datetime import datetime


def generate_summary_pdf(summary: dict) -> bytes:
    """
    Render *summary* dict as a downloadable PDF using ReportLab.

    Returns raw PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore[import]
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT
    except ImportError as exc:
        raise RuntimeError("reportlab is not installed") from exc

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    body_style = styles["BodyText"]
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=(0.4, 0.4, 0.4),
        spaceAfter=4,
    )

    created_at = summary.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%Y-%m-%d %H:%M UTC")

    keywords = summary.get("keywords") or []
    keyword_str = ", ".join(keywords) if keywords else "—"

    story = [
        Paragraph("Summary Report", title_style),
        Spacer(1, 0.4 * cm),
        Paragraph(f"<b>Source:</b> {summary.get('source_type', '').upper()}", meta_style),
        Paragraph(f"<b>Length:</b> {summary.get('summary_length', '')} | <b>Format:</b> {summary.get('format', '')}", meta_style),
        Paragraph(f"<b>Words:</b> {summary.get('word_count', '')} | <b>Language:</b> {summary.get('language', '')}", meta_style),
        Paragraph(f"<b>Model:</b> {summary.get('model_used', '')} | <b>Tokens:</b> {summary.get('tokens_used', '—')}", meta_style),
        Paragraph(f"<b>Created:</b> {created_at}", meta_style),
        Spacer(1, 0.5 * cm),
        Paragraph("<b>Keywords</b>", styles["Heading2"]),
        Paragraph(keyword_str, body_style),
        Spacer(1, 0.5 * cm),
        Paragraph("<b>Summary</b>", styles["Heading2"]),
        Spacer(1, 0.2 * cm),
        Paragraph(summary.get("summary", "").replace("\n", "<br/>"), body_style),
    ]

    doc.build(story)
    return buf.getvalue()
