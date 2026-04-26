from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.domain.errors import BusinessRuleViolation, ConflictError, NotFoundError, ValidationError
from app.infrastructure.config import settings
from app.presentation.routers.categories import router as categories_router
from app.presentation.routers.equipments import router as equipment_router

_FRONTEND_DIR = Path("frontend")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "validation_error"},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "not_found"},
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "conflict"},
        )

    @app.exception_handler(BusinessRuleViolation)
    async def business_rule_handler(_request: Request, exc: BusinessRuleViolation) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "business_rule_violation"},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(categories_router)
    app.include_router(equipment_router)

    if _FRONTEND_DIR.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(_FRONTEND_DIR / "static")),
            name="static",
        )

        @app.get("/", include_in_schema=False)
        async def serve_index() -> FileResponse:
            return FileResponse(str(_FRONTEND_DIR / "index.html"))

    return app


app = create_app()
