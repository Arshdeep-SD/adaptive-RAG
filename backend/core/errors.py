from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def _error_body(code: str, message: str, details: dict) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_error_body("NOT_FOUND", "Resource not found", {}),
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred", {}),
        )
