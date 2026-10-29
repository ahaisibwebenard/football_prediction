import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError
from fastapi import Depends
from backend.db import get_db
from backend.models.entities import Setting
from backend.config import ROOT, ENV, HOSTS, URL
from backend.routes import auth, user, admin

app = FastAPI(
    title="PredictPro API",
    version="1.0.0",
    docs_url="/api/docs" if ENV != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if ENV != "production" else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=HOSTS)


@app.middleware("http")
async def harden(request: Request, call_next):
    length = request.headers.get("content-length", "0")
    if length.isdigit() and int(length) > 65536:
        return JSONResponse({"detail": "Request too large."}, 413)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") not in (None, URL):
            return JSONResponse({"detail": "Origin rejected."}, 403)
    try:
        response = await call_next(request)
    except Exception:
        logging.exception("Unhandled request error")
        response = JSONResponse({"detail": "An unexpected error occurred."}, 500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if ENV != "production" and request.url.path == "/api/docs":
        # Only the optional developer docs load Swagger UI from its CDN.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    if ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(IntegrityError)
async def integrity(request, exc):
    return JSONResponse(
        {
            "detail": "Conflicting or referenced record. Check unique fields and delete dependent records first."
        },
        409,
    )


@app.exception_handler(RequestValidationError)
async def validation(request, exc):
    return JSONResponse(
        {"detail": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]},
        422,
    )


@app.get("/api/site")
def site(db=Depends(get_db, scope="function")):
    name = db.get(Setting, "site_name")
    return {"site_name": name.value if name else "PredictPro"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PredictPro"}


@app.get("/")
def index():
    return FileResponse(ROOT / "frontend" / "index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")
