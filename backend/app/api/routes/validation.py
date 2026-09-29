"""
Pre-Publish Tender Validation API Routes for SIH26108 (Feature M10).
Provides deterministic validation of tender specifications prior to publication.

Endpoints:
- POST /api/pre-publish/validate
- GET  /api/pre-publish/validate/{validation_id}
- POST /api/pre-publish/validate/{validation_id}/review
- GET  /api/pre-publish/validate/{validation_id}/download
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import html
import logging

from backend.app.schemas.dtos import (
    TenderValidationRequest,
    TenderValidationReport,
    ValidationReviewRequest,
    OfficerReviewDecision
)
from backend.app.api.dependencies import get_database, get_tender_validator
from backend.app.models.entities import Document, DocumentChunk, TenderValidationRecord
from ai_engine.validation.tender_validator import TenderValidator, ADVISORY_DISCLAIMER

logger = logging.getLogger("sih26108.validation_route")
router = APIRouter(prefix="/pre-publish", tags=["Pre-Publish Tender Validation"])

MAX_TEXT_LENGTH = 1_000_000  # 1MB text limit


@router.post("/validate", response_model=TenderValidationReport)
def validate_tender(
    payload: TenderValidationRequest,
    db: Session = Depends(get_database),
    validator: TenderValidator = Depends(get_tender_validator)
):
    """
    Validates technical specifications against verified Indian Standards catalogue,
    official QCO registry, normative reference relations, and foreign standard policies.
    Accepts either direct text or an existing uploaded document_id.
    """
    text_to_validate: str = ""
    document_chunks: Optional[List[Dict[str, Any]]] = None
    doc_id: Optional[str] = payload.document_id

    # 1. Validate Input Presence
    if not payload.tender_text and not payload.document_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'tender_text' or 'document_id' must be provided."
        )

    # 2. Resolve Text Source
    if payload.document_id:
        db_doc = db.query(Document).filter(Document.id == payload.document_id).first()
        if not db_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded document '{payload.document_id}' not found."
            )

        db_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == payload.document_id)
            .order_by(DocumentChunk.page_number)
            .all()
        )
        if not db_chunks:
            raise HTTPException(
                status_code=400,
                detail=f"Document '{payload.document_id}' has no extracted text chunks available."
            )

        document_chunks = [
            {
                "chunk_id": c.id,
                "page_number": c.page_number,
                "section": c.section,
                "content": c.content
            }
            for c in db_chunks
        ]
        text_to_validate = "\n\n".join([c["content"] for c in document_chunks if c["content"]])
        if not text_to_validate.strip():
            raise HTTPException(
                status_code=400,
                detail="Extracted text from document chunks is empty."
            )
    else:
        text_to_validate = payload.tender_text or ""
        if not text_to_validate.strip():
            raise HTTPException(
                status_code=400,
                detail="Tender text cannot be empty or whitespace only."
            )
        if len(text_to_validate) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Tender text exceeds the maximum permitted limit of {MAX_TEXT_LENGTH} characters."
            )

    # 3. Execute Deterministic Validation
    try:
        report_data = validator.validate(
            text=text_to_validate,
            document_chunks=document_chunks,
            document_id=doc_id
        )
    except Exception as exc:
        logger.error("Validation execution failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation error: {str(exc)}")

    # 4. Persist Validation Audit Record
    try:
        snippet = text_to_validate[:400] + ("..." if len(text_to_validate) > 400 else "")
        record = TenderValidationRecord(
            id=report_data["validation_id"],
            document_id=doc_id,
            input_text_snippet=snippet,
            report_json=report_data,
            overall_status=report_data["overall_status"],
            officer_status="PENDING",
            created_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to persist validation record (non-fatal): %s", exc)

    return TenderValidationReport(**report_data)


@router.get("/validate/{validation_id}", response_model=TenderValidationReport)
def get_validation_report(
    validation_id: str,
    db: Session = Depends(get_database)
):
    """Retrieves a previously generated pre-publish validation report by its ID."""
    record = db.query(TenderValidationRecord).filter(TenderValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Validation report '{validation_id}' not found.")

    report_data = dict(record.report_json)
    # Ensure officer review sync with entity fields
    if record.officer_status != "PENDING" and record.officer_id:
        report_data["officer_review_status"] = record.officer_status
        report_data["officer_review"] = {
            "reviewer_id": record.officer_id,
            "decision": record.officer_status,
            "comments": record.officer_comments or "",
            "reviewed_at": record.reviewed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if record.reviewed_at else None
        }

    return TenderValidationReport(**report_data)


@router.post("/validate/{validation_id}/review", response_model=TenderValidationReport)
def review_validation_report(
    validation_id: str,
    payload: ValidationReviewRequest,
    db: Session = Depends(get_database)
):
    """
    Records official procurement officer review outcome and notes.
    Decisions: APPROVED_WITH_NOTES, AMENDMENT_REQUESTED, REJECTED.
    """
    valid_decisions = ["APPROVED_WITH_NOTES", "AMENDMENT_REQUESTED", "REJECTED"]
    decision = payload.decision.strip().upper()
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid review decision '{payload.decision}'. Allowed decisions: {valid_decisions}"
        )

    record = db.query(TenderValidationRecord).filter(TenderValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Validation report '{validation_id}' not found.")

    now = datetime.utcnow()
    officer_id = payload.officer_id or "DEV_OFFICER_DEFAULT"
    comments = payload.comments or ""

    record.officer_status = decision
    record.officer_id = officer_id
    record.officer_comments = comments
    record.reviewed_at = now

    report_data = dict(record.report_json)
    report_data["officer_review_status"] = decision
    report_data["officer_review"] = {
        "reviewer_id": officer_id,
        "decision": decision,
        "comments": comments,
        "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    record.report_json = report_data

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record officer review: {str(exc)}")

    return TenderValidationReport(**report_data)


@router.get("/validate/{validation_id}/download")
def download_validation_report(
    validation_id: str,
    db: Session = Depends(get_database)
):
    """Downloads an official executive HTML Pre-Publish Validation Report."""
    record = db.query(TenderValidationRecord).filter(TenderValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Validation report '{validation_id}' not found.")

    html_content = render_validation_html_report(record.report_json)
    filename = f"pre_publish_validation_{validation_id}.html"

    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        }
    )


# ─── HTML Report Generator ──────────────────────────────────────────────────

def render_validation_html_report(data: Dict[str, Any]) -> str:
    """Renders a print-ready, executive HTML Pre-Publish Validation Report."""
    val_id = html.escape(data.get("validation_id", "N/A"))
    timestamp = html.escape(data.get("timestamp", "N/A"))
    doc_id = html.escape(data.get("document_id") or "Direct Specification Text")
    overall_status = data.get("overall_status", "OFFICER_REVIEW_REQUIRED")
    summary = data.get("summary_counts", {})
    findings = data.get("findings", [])
    completed = data.get("checks_completed", [])
    not_completed = data.get("checks_not_completed", [])
    limitations = data.get("data_limitations", [])
    disclaimer = html.escape(data.get("advisory_disclaimer", ADVISORY_DISCLAIMER))
    officer_review = data.get("officer_review")

    status_colors = {
        "REQUIRES_AMENDMENT": ("#ef4444", "#fef2f2", "#991b1b", "Requires Amendment"),
        "OFFICER_REVIEW_REQUIRED": ("#f59e0b", "#fffbeb", "#92400e", "Officer Review Required"),
        "NO_BLOCKING_ISSUES_DETECTED": ("#10b981", "#ecfdf5", "#065f46", "No Blocking Issues Detected")
    }
    border_col, bg_col, text_col, status_label = status_colors.get(
        overall_status,
        ("#64748b", "#f8fafc", "#334155", overall_status)
    )

    # Group findings by severity
    findings_by_sev = {
        "CRITICAL": [f for f in findings if f.get("severity") == "CRITICAL"],
        "WARNING": [f for f in findings if f.get("severity") == "WARNING"],
        "MANUAL_REVIEW_REQUIRED": [f for f in findings if f.get("severity") == "MANUAL_REVIEW_REQUIRED"],
        "INFO": [f for f in findings if f.get("severity") == "INFO"]
    }

    def render_finding_card(f: Dict[str, Any]) -> str:
        fid = html.escape(f.get("id", ""))
        rule_name = html.escape(f.get("rule_name", ""))
        desc = html.escape(f.get("description", ""))
        rec_action = html.escape(f.get("recommended_action", ""))
        excerpt = html.escape(f.get("clause_excerpt") or "N/A")
        std_id = html.escape(f.get("standard_identifier") or "None Identified")
        ev_src = html.escape(f.get("evidence_source") or "Catalogue Record")
        ev_text = html.escape(f.get("evidence_excerpt") or "No excerpt available")
        conf = html.escape(f.get("confidence_status", "VERIFIED_FACT"))
        sev = f.get("severity", "INFO")

        badge_col = "#dc2626" if sev == "CRITICAL" else ("#d97706" if sev == "WARNING" else ("#7c3aed" if sev == "MANUAL_REVIEW_REQUIRED" else "#2563eb"))

        return f"""
        <div style="border: 1px solid #e2e8f0; border-left: 4px solid {badge_col}; border-radius: 6px; padding: 12px; margin-bottom: 12px; background: #ffffff;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-weight: 700; font-size: 13px; color: #1e293b;">{rule_name} <span style="font-size: 11px; font-weight: normal; color: #64748b;">({fid})</span></div>
            <span style="background: {badge_col}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;">{sev}</span>
          </div>
          <p style="font-size: 13px; margin: 4px 0 8px 0; color: #0f172a; line-height: 1.4;">{desc}</p>
          <div style="background: #f8fafc; padding: 8px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 6px;">
            <div style="font-weight: 600; color: #475569;">Tender Excerpt:</div>
            <div style="font-style: italic; color: #334155;">&ldquo;{excerpt}&rdquo;</div>
          </div>
          <div style="font-size: 12px; color: #0369a1; background: #f0f9ff; padding: 8px 10px; border-radius: 4px; margin-bottom: 6px;">
            <strong>Recommended Action:</strong> {rec_action}
          </div>
          <div style="font-size: 11px; color: #64748b; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; border-top: 1px solid #f1f5f9; padding-top: 6px;">
            <div><strong>Standard:</strong> {std_id} | <strong>Source:</strong> {ev_src}</div>
            <div><strong>Confidence:</strong> <code>{conf}</code></div>
          </div>
          <div style="font-size: 11px; color: #475569; margin-top: 4px;">
            <strong>Evidence:</strong> {ev_text}
          </div>
        </div>
        """

    def render_section(title: str, items: List[Dict[str, Any]], color: str) -> str:
        if not items:
            return ""
        cards = "\n".join([render_finding_card(f) for f in items])
        return f"""
        <div style="margin-bottom: 20px;">
          <h3 style="font-size: 14px; font-weight: 700; color: {color}; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 12px;">
            {title} ({len(items)})
          </h3>
          {cards}
        </div>
        """

    findings_html = (
        render_section("Critical Findings — Blocking Amendment Required", findings_by_sev["CRITICAL"], "#dc2626") +
        render_section("Warnings — Officer Review Required", findings_by_sev["WARNING"], "#d97706") +
        render_section("Manual Review Required — Unverified Elements", findings_by_sev["MANUAL_REVIEW_REQUIRED"], "#7c3aed") +
        render_section("Informational & Verified Standards", findings_by_sev["INFO"], "#2563eb")
    )
    if not findings_html:
        findings_html = "<p style='color: #64748b; font-size: 13px;'>No specific findings recorded.</p>"

    # Officer review section
    if officer_review:
        rev_decision = html.escape(officer_review.get("decision", "N/A"))
        rev_officer = html.escape(officer_review.get("reviewer_id", "N/A"))
        rev_comments = html.escape(officer_review.get("comments") or "No comments provided.")
        rev_at = html.escape(officer_review.get("reviewed_at", "N/A"))
        officer_html = f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
          <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Recorded Officer Decision: <code>{rev_decision}</code></div>
          <div style="font-size: 12px; color: #475569; margin-bottom: 4px;"><strong>Reviewer Identity:</strong> {rev_officer} (Logged Reviewer ID) &bull; <strong>Timestamp:</strong> {rev_at}</div>
          <div style="font-size: 12px; color: #334155; background: #ffffff; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0;">
            <strong>Officer Comments:</strong> {rev_comments}
          </div>
        </div>
        """
    else:
        officer_html = """
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 16px; color: #64748b; font-size: 12px;">
          <em>Pending Officer Review. No procurement officer decision has been finalized for this validation session.</em>
        </div>
        """

    completed_list = "".join([f"<li style='margin-bottom: 4px;'>{html.escape(c)}</li>" for c in completed])
    not_completed_list = "".join([f"<li style='margin-bottom: 4px;'>{html.escape(nc)}</li>" for nc in not_completed])
    limitations_list = "".join([f"<li style='margin-bottom: 4px;'>{html.escape(lim)}</li>" for lim in limitations])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pre-Publish Validation Report - {val_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #0f172a; margin: 0; padding: 24px; background: #ffffff; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .btn-print {{ background: #1e3a8a; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 12px; }}
  .card {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
  .card-title {{ font-size: 14px; font-weight: 700; color: #1e3a8a; margin-top: 0; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ padding: 0; }}
    .card {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; background: #f1f5f9; padding: 10px 16px; border-radius: 8px;">
    <span style="font-size: 12px; color: #475569;">Technical Pre-Publish Validation &bull; ID: <code>{val_id}</code></span>
    <button class="btn-print" onclick="window.print()">🖨️ Print or Save as PDF</button>
  </div>

  <!-- Header -->
  <div style="border-bottom: 3px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start;">
    <div>
      <div style="font-size: 11px; font-weight: 800; letter-spacing: 1.5px; color: #b45309; text-transform: uppercase;">GOVERNMENT PROCUREMENT DECISION SUPPORT</div>
      <h1 style="font-size: 22px; margin: 4px 0 4px 0; color: #1e3a8a;">Pre-Publish Validation Report</h1>
      <div style="font-size: 12px; color: #64748b;">Statutory Indian Standard and QCO Adherence Verification</div>
    </div>
    <div style="text-align: right; font-size: 11px; color: #64748b;">
      <div><strong>Validation ID:</strong> <code>{val_id}</code></div>
      <div><strong>Date:</strong> {timestamp}</div>
      <div><strong>Document Reference:</strong> {doc_id}</div>
    </div>
  </div>

  <!-- Mandatory Advisory Notice -->
  <div style="background: #fffbeb; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px 14px; margin-bottom: 20px; font-size: 12px; color: #92400e; line-height: 1.45;">
    <strong>⚠️ MANDATORY ADVISORY NOTICE:</strong><br>
    {disclaimer}
  </div>

  <!-- Overall Workflow Status Banner -->
  <div style="background: {bg_col}; border: 2px solid {border_col}; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
      <div style="font-size: 11px; font-weight: 700; color: {text_col}; text-transform: uppercase;">Overall Automated Workflow Status</div>
      <div style="font-size: 18px; font-weight: 800; color: {text_col}; margin-top: 2px;">{status_label}</div>
    </div>
    <div style="display: flex; gap: 12px; text-align: center;">
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;">
        <div style="font-size: 18px; font-weight: 800; color: #dc2626;">{summary.get("CRITICAL", 0)}</div>
        <div style="font-size: 10px; color: #64748b; font-weight: 600;">CRITICAL</div>
      </div>
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;">
        <div style="font-size: 18px; font-weight: 800; color: #d97706;">{summary.get("WARNING", 0)}</div>
        <div style="font-size: 10px; color: #64748b; font-weight: 600;">WARNING</div>
      </div>
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;">
        <div style="font-size: 18px; font-weight: 800; color: #7c3aed;">{summary.get("MANUAL_REVIEW_REQUIRED", 0)}</div>
        <div style="font-size: 10px; color: #64748b; font-weight: 600;">MANUAL REV</div>
      </div>
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;">
        <div style="font-size: 18px; font-weight: 800; color: #2563eb;">{summary.get("INFO", 0)}</div>
        <div style="font-size: 10px; color: #64748b; font-weight: 600;">INFO</div>
      </div>
    </div>
  </div>

  <!-- Officer Decision Section -->
  <div class="card">
    <div class="card-title">1. Procurement Officer Review Status</div>
    {officer_html}
  </div>

  <!-- Detailed Findings -->
  <div class="card">
    <div class="card-title">2. Automated Validation Findings</div>
    {findings_html}
  </div>

  <!-- Checks Completed & Not Completed -->
  <div class="card">
    <div class="card-title">3. Audit Scope & Verification Boundary</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px;">
      <div>
        <h4 style="margin: 0 0 6px 0; color: #059669; font-size: 12px;">✓ Checks Completed</h4>
        <ul style="margin: 0; padding-left: 18px; color: #334155;">
          {completed_list}
        </ul>
      </div>
      <div>
        <h4 style="margin: 0 0 6px 0; color: #dc2626; font-size: 12px;">✗ Checks Not Completed / Out of Scope</h4>
        <ul style="margin: 0; padding-left: 18px; color: #64748b;">
          {not_completed_list}
        </ul>
      </div>
    </div>
  </div>

  <!-- Data Limitations -->
  <div class="card">
    <div class="card-title">4. Dataset Limitations & Scope Constraints</div>
    <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #475569;">
      {limitations_list}
    </ul>
  </div>

  <!-- Bottom Legal Footer -->
  <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 24px; text-align: center; font-size: 11px; color: #94a3b8;">
    Smart India Hackathon 2026 &bull; Problem Statement SIH26108 &bull; Bureau of Indian Standards (BIS) SpecEngine<br>
    <em>This pre-publish document is an internal advisory artifact and does not replace statutory administrative procurement sanction.</em>
  </div>
</div>
</body>
</html>
"""
