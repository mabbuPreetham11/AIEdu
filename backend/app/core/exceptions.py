from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class LMSException(HTTPException):
    pass


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LMSException)
    async def lms_exception_handler(_: Request, exc: LMSException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})
