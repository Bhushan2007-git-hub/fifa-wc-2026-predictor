"""FIFA World Cup 2026 Predictor — FastAPI Backend"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api.routes import router, get_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading ML model and all datasets...")
    get_state()
    print("Ready.")
    yield


app = FastAPI(
    title="FIFA WC 2026 Predictor",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"app": "FIFA WC 2026 Predictor", "docs": "/docs", "version": "3.0.0"}
