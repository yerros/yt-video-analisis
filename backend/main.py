"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import jobs, stream, frames, statistics, chat, worker

app = FastAPI(
    title="Video Analysis AI API",
    description="API untuk analisa konten video YouTube menggunakan AI multimodal",
    version="0.1.0",
)

# CORS middleware
# Allow all origins for Docker deployment across different networks
# In production, you should restrict this to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (customize for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(stream.router, prefix="/api/jobs", tags=["stream"])
app.include_router(frames.router, prefix="/api", tags=["frames"])
app.include_router(statistics.router, prefix="/api", tags=["statistics"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(worker.router, prefix="/api/worker", tags=["worker"])


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "Video Analysis AI API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
