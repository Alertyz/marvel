"""Sync API — Android app connects to PC through these endpoints.

Endpoints:
  GET  /sync/handshake     — App discovers PC, gets server info
  GET  /sync/state         — Pull full state (progress, reports, settings)
  POST /sync/state         — Push state from app (merges with PC data)
  GET  /sync/catalog       — List of issues with images available on PC
  GET  /sync/issue/{order}/pages  — List pages available for an issue
  GET  /sync/issue/{order}/page/{page}  — Download a single page image
"""
import os
import re
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from ..database import ReaderDB
from ..config import COMICS_DIR

router = APIRouter()
db = ReaderDB()


@router.get("/handshake")
def handshake():
    """App calls this to verify PC is reachable and get basic info."""
    stats = db.get_stats()
    available = db.get_available_issues()
    return {
        "server": "marvel-reader",
        "version": db.get_sync_version(),
        "total_issues": stats["total_issues"],
        "available_issues": len(available),
        "read_issues": stats["read_issues"],
    }


@router.get("/state")
def get_sync_state():
    """Pull full sync state — progress, reports, settings."""
    return db.get_sync_state()


@router.post("/state")
def push_sync_state(payload: dict = Body(...)):
    """Push state from app. Merges progress (last-write-wins), reports, settings."""
    progress = payload.get("progress", [])
    reports = payload.get("reports", [])
    settings = payload.get("settings", {})
    if not isinstance(progress, list):
        raise HTTPException(400, "progress must be a list")
    new_version = db.apply_sync_state(progress, reports, settings)
    # Return merged state so app can update
    return {
        "version": new_version,
        "state": db.get_sync_state(),
    }


@router.get("/catalog")
def get_catalog():
    """List all issues that have images on PC, with page counts.
    App uses this to know what's available for download."""
    library = db.get_library()
    available = {i["order_num"]: i["pages"] for i in db.get_available_issues()}
    result = []
    for iss in library:
        result.append({
            "order_num": iss["order_num"],
            "title": iss["title"],
            "issue": iss["issue"],
            "phase": iss["phase"],
            "event": iss["event"],
            "year": iss["year"],
            "available_pages": available.get(iss["order_num"], 0),
        })
    return result


@router.get("/issue/{order_num}/pages")
def get_issue_pages(order_num: int):
    """List all available page numbers for an issue."""
    issue = db.get_issue(order_num)
    if not issue:
        raise HTTPException(404, "Issue not found")
    safe = re.sub(r'[<>:"/\\|?*]', '_', issue["title"])
    issue_dir = COMICS_DIR / safe / f"Issue_{issue['issue']:03d}"
    if not issue_dir.exists():
        return {"order_num": order_num, "pages": []}

    pages = []
    for f in sorted(issue_dir.iterdir()):
        if f.suffix.lower() in (".jpg", ".png", ".webp"):
            # Extract page number from filename like page_001.jpg
            match = re.match(r'page_(\d+)', f.stem)
            if match:
                pages.append({
                    "page_num": int(match.group(1)),
                    "filename": f.name,
                    "size": f.stat().st_size,
                })
    return {"order_num": order_num, "pages": pages}


@router.get("/issue/{order_num}/page/{page_num}")
def download_page(order_num: int, page_num: int):
    """Download a single page image. App calls this to fetch images from PC."""
    fpath = db.get_issue_page_path(order_num, page_num)
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(404, "Page not found")

    real_path = os.path.realpath(fpath)
    comics_real = os.path.realpath(str(COMICS_DIR))
    if not real_path.startswith(comics_real):
        raise HTTPException(403, "Access denied")

    return FileResponse(
        real_path,
        headers={"Cache-Control": "no-cache"},
    )
