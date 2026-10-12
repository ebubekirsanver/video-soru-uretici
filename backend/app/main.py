from fastapi import FastAPI

from app.config import get_settings
from app.routers import router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="YouTube ders videolarından doğrulanabilir soru üretimi",
    version="0.1.0",
)


app.include_router(router)


@app.get("/health", tags=["sistem"])
def health() -> dict[str, str]:
    """Servisin ayakta olduğunu doğrular."""
    return {"status": "ok"}
