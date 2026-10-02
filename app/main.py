
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.firebase import initialize_firebase

from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase()
    yield


app = FastAPI(
    title="TourKare API",
    description="AI-powered travel itinerary generation API",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS configuration for Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TourKare API",
    }