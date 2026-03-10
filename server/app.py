from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
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


@app.get("/icon-192.png")
async def icon_192():
    return FileResponse(str(BASE_DIR / "web" / "icon-192.png"),
                        media_type="image/png",
                        headers={"Cache-Control": "public, max-age=604800"})


@app.get("/icon-512.png")
async def icon_512():
    return FileResponse(str(BASE_DIR / "web" / "icon-512.png"),
                        media_type="image/png",
                        headers={"Cache-Control": "public, max-age=604800"})


@app.get("/cert")
async def download_cert():
    """Download the self-signed certificate for mobile trust installation."""
    cert_path = BASE_DIR / ".certs" / "cert.pem"
    if cert_path.exists():
        return FileResponse(
            str(cert_path),
            media_type="application/x-pem-file",
            filename="marvel-reader-cert.pem",
            headers={"Content-Disposition": "attachment; filename=marvel-reader-cert.pem"},
        )
    return Response(content="Certificate not found", status_code=404)


@app.get("/download-apk")
async def download_apk():
    """Serve the built APK for mobile installation."""
    apk_path = BASE_DIR / "web" / "marvel-reader.apk"
    if apk_path.exists():
        return FileResponse(
            str(apk_path),
            media_type="application/vnd.android.package-archive",
            filename="MarvelReader.apk",
        )
    return Response(
        content="APK ainda não foi compilado. Execute: python build_apk.py",
        status_code=404,
    )
