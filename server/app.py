from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import BASE_DIR
from .routers import api

app = FastAPI(title="Marvel Comic Reader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")


@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "web" / "index.html"))


@app.get("/reading-order")
async def reading_order_page():
    path = BASE_DIR / "web" / "reading_order.html"
    if path.exists():
        return FileResponse(str(path))
    return {"error": "reading_order.html not found"}


@app.get("/sw.js")
async def service_worker():
    path = BASE_DIR / "web" / "sw.js"
    if path.exists():
        return FileResponse(str(path), media_type="application/javascript",
                            headers={"Cache-Control": "no-cache",
                                     "Service-Worker-Allowed": "/"})
    return FileResponse(str(path))


@app.get("/manifest.json")
async def manifest():
    return FileResponse(str(BASE_DIR / "web" / "manifest.json"),
                        media_type="application/manifest+json")
