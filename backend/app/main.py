from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import router

settings = get_settings()

# Tarayıcıdan yalnızca yerel Next.js geliştirme sunucusu backend'e istek atabilir.
# Bilerek ortam değişkeninden okunmuyor: başka bir kaynağa izin vermek kod değişikliği gerektirsin.
ALLOWED_ORIGINS = ["http://localhost:3000"]

app = FastAPI(
    title=settings.app_name,
    description="YouTube ders videolarından doğrulanabilir soru üretimi",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.include_router(router)


@app.get("/health", tags=["sistem"])
def health() -> dict[str, str]:
    """Servisin ayakta olduğunu doğrular."""
    return {"status": "ok"}
