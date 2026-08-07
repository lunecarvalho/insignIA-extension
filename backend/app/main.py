from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .core.logging import logger
from .models import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from .services.analyzer import Analyzer, AnalyzerError, build_analyzer_from_settings

app = FastAPI(title="InsignIA API", version="1.0.0")

_analyzer: Analyzer | None = None


def get_analyzer() -> Analyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = build_analyzer_from_settings(settings)
    return _analyzer

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AnalyzerError)
async def analyzer_error_handler(_: Request, exc: AnalyzerError):
    logger.exception("Analyzer error")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled API error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="Erro interno ao processar a requisição.",
            detail=str(exc),
        ).model_dump(),
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest):
    analyzer = get_analyzer()
    return analyzer.analyze(payload)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting InsignIA API")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down InsignIA API")
