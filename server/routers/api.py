import re
import os
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from ..database import ReaderDB
from ..config import COMICS_DIR

router = APIRouter()
db = ReaderDB()


@router.get("/library")
def get_library(phase: str = None, series: str = None, search: str = None):
    return db.get_library(phase=phase, series=series, search=search)


@router.get("/eras")
def get_eras():
    return db.get_eras()


@router.get("/series")
def get_series():
    return db.get_series_list()


@router.get("/stats")
def get_stats():
    return db.get_stats()


@router.get("/bookmark")
def get_bookmark():
    bm = db.get_bookmark()
    if not bm:
        return {"message": "All read!", "order_num": None}
    return bm


@router.get("/issues/{order_num}")
def get_issue(order_num: int):
    issue = db.get_issue(order_num)
    if not issue:
        raise HTTPException(404, "Issue not found")
    issue["available_pages"] = db.get_issue_page_count(order_num)
    return issue


@router.get("/issues/{order_num}/page/{page_num}")
def get_page_image(order_num: int, page_num: int):
    """Serve a comic page image securely by constructing the path from issue data."""
    fpath = db.get_issue_page_path(order_num, page_num)
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(404, "Page not found")

    # Verify the resolved path is under COMICS_DIR
    real_path = os.path.realpath(fpath)
    comics_real = os.path.realpath(str(COMICS_DIR))
    if not real_path.startswith(comics_real):
        raise HTTPException(403, "Access denied")

    return FileResponse(real_path, headers={"Cache-Control": "public, max-age=86400"})


@router.post("/progress/{order_num}")
def update_progress(
    order_num: int,
    current_page: int = Query(None),
    is_read: bool = Query(None),
):
    issue = db.get_issue(order_num)
    if not issue:
        raise HTTPException(404, "Issue not found")
    db.update_progress(order_num, current_page=current_page, is_read=is_read)
    return {"ok": True}


@router.post("/progress/{order_num}/toggle-read")
def toggle_read(order_num: int):
    issue = db.get_issue(order_num)
    if not issue:
        raise HTTPException(404, "Issue not found")
    new_state = db.toggle_read(order_num)
    return {"is_read": new_state}


@router.post("/progress/mark-before/{order_num}")
def mark_all_before(order_num: int):
    count = db.mark_all_before_as_read(order_num)
    return {"marked": count}


# ── Sync ──────────────────────────────────────────────────
@router.get("/sync/version")
def get_sync_version():
    return {"version": db.get_sync_version()}


@router.get("/sync/state")
def get_sync_state():
    return db.get_sync_state()


@router.post("/sync/state")
def push_sync_state(payload: dict = Body(...)):
    progress = payload.get("progress", [])
    if not isinstance(progress, list):
        raise HTTPException(400, "progress must be a list")
    new_version = db.apply_sync_state(progress)
    return {"version": new_version, "ok": True}


# ── Reports ───────────────────────────────────────────────
REPORT_TYPES = {"missing_images", "wrong_order", "bad_quality", "wrong_issue", "other"}


@router.post("/reports")
def create_report(payload: dict = Body(...)):
    issue_order = payload.get("issue_order")
    page_num = payload.get("page_num")
    report_type = payload.get("report_type", "other")
    description = payload.get("description", "")
    if not issue_order:
        raise HTTPException(400, "issue_order is required")
    if report_type not in REPORT_TYPES:
        raise HTTPException(400, f"report_type must be one of {REPORT_TYPES}")
    issue = db.get_issue(issue_order)
    if not issue:
        raise HTTPException(404, "Issue not found")
    rid = db.add_report(issue_order, page_num, report_type, description[:500] if description else "")
    return {"id": rid, "ok": True}


@router.get("/reports")
def get_reports(resolved: bool = None):
    return db.get_reports(resolved=resolved)


@router.get("/reports/flagged")
def get_flagged_issues():
    return list(db.get_flagged_issues())


@router.get("/issues/{order_num}/reports")
def get_issue_reports(order_num: int):
    return db.get_issue_reports(order_num)


@router.post("/reports/{report_id}/resolve")
def resolve_report(report_id: int):
    db.resolve_report(report_id)
    return {"ok": True}


@router.delete("/reports/{report_id}")
def delete_report(report_id: int):
    db.delete_report(report_id)
    return {"ok": True}
