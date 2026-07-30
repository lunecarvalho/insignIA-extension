from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .core.logging import logger
from .controllers import router

app = FastAPI(title="InsignIA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting InsignIA API")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down InsignIA API")
