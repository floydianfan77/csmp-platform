from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import duckdb
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from csmp_monitor.config import settings
from csmp_monitor.repository import MonitorRepository
from csmp_monitor.schemas import ErrorResponse, HealthResponse, IntersectionListResponse, IntersectionStatus


def create_app(*, repository: MonitorRepository | None = None) -> FastAPI:
    owned: dict[str, duckdb.DuckDBPyConnection | None] = {"con": None}

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if repository is not None:
            app.state.repository = repository
        else:
            owned["con"] = duckdb.connect(settings.duckdb_path, read_only=True)
            app.state.repository = MonitorRepository.from_connection(owned["con"])
        yield
        if owned["con"] is not None:
            owned["con"].close()

    app = FastAPI(title="CSMP Monitor API", version="1.0.0", lifespan=lifespan)

    @app.get("/health", response_model=HealthResponse)
    def get_health(request: Request) -> HealthResponse:
        return request.app.state.repository.health(
            threshold_seconds=settings.freshness_threshold_seconds
        )

    @app.get("/intersections", response_model=IntersectionListResponse)
    def list_intersections(
        request: Request,
        bottleneck_only: bool = False,
    ) -> IntersectionListResponse:
        items = request.app.state.repository.list_latest(bottleneck_only=bottleneck_only)
        return IntersectionListResponse(count=len(items), items=items)

    @app.get(
        "/intersections/{intersection_id}",
        response_model=IntersectionStatus,
        responses={404: {"model": ErrorResponse}},
    )
    def get_intersection(request: Request, intersection_id: str):
        item = request.app.state.repository.get_latest(intersection_id)
        if item is None:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(
                    code="NOT_FOUND",
                    message=f"Unknown intersection: {intersection_id}",
                ).model_dump(),
            )
        return item

    return app


app = create_app()
