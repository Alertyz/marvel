from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import BASE_DIR
from .routers import api, sync

app = FastAPI(title="Marvel Comic Reader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(sync.router, prefix="/sync")


@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "web" / "index.html"))
