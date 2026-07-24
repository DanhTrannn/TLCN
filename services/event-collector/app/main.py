import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.schemas.event import AcceptedEvent, WebEvent
from app.service import EventIngestor
from app.writer.jsonl_writer import JsonlWriter

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    writer = JsonlWriter(
        directory=settings.event_directory,
        max_bytes=settings.rotation_max_bytes,
        max_age_seconds=settings.rotation_max_age_seconds,
    )
    app.state.writer = writer
    app.state.ingestor = EventIngestor(
        writer=writer,
        service_version=settings.service_version,
        dedup_window_seconds=settings.dedup_window_seconds,
        dedup_max_entries=settings.dedup_max_entries,
    )
    yield
    writer.close()


app = FastAPI(
    title="TLCN Event Collector",
    version=settings.service_version,
    lifespan=lifespan,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready() -> dict[str, str]:
    directory = settings.event_directory
    if not directory.exists() or not os.access(directory, os.W_OK):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="event_directory_not_ready",
        )
    return {"status": "ready"}


@app.post(
    "/events/v1/events",
    response_model=AcceptedEvent,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["events"],
)
def collect(event: WebEvent, request: Request) -> AcceptedEvent:
    duplicate = request.app.state.ingestor.ingest(event)
    return AcceptedEvent(event_id=event.event_id, duplicate=duplicate)
