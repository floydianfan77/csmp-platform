from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import duckdb
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from csmp_monitor.config import settings
from csmp_monitor.repository import MonitorRepository
from csmp_monitor.schemas import ErrorResponse, HealthResponse, IntersectionListResponse, IntersectionStatus

UI_STATIC_DIR = (
    Path(__file__).resolve().parents[3] / "monitor-ui" / "static"
)


def _mount_ui(app: FastAPI) -> None:
    if not UI_STATIC_DIR.is_dir():
        return
    from fastapi.responses import RedirectResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/app", StaticFiles(directory=str(UI_STATIC_DIR), html=True), name="monitor-ui")

    @app.get("/", include_in_schema=False)
    def redirect_to_ui():
        return RedirectResponse(url="/app/")


def _open_duckdb_readonly() -> duckdb.DuckDBPyConnection:
    path = Path(settings.duckdb_path)
    if not path.is_file():
        landing = path.parent / "landing.db"
        hint = (
            f"DuckDB file not found: {path}\n"
            f"Run from project root: .\\Makefile.ps1 warehouse\n"
            f"Or full pipeline: .\\Makefile.ps1 demo"
        )
        if landing.is_file():
            hint = (
                f"DuckDB file not found: {path}\n"
                f"landing.db exists — run: .\\Makefile.ps1 warehouse"
            )
        raise FileNotFoundError(hint)
    return duckdb.connect(str(path), read_only=True)


def create_app(*, repository: MonitorRepository | None = None) -> FastAPI:
    owned: dict[str, duckdb.DuckDBPyConnection | None] = {"con": None}

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if repository is not None:
            app.state.repository = repository
        else:
            owned["con"] = _open_duckdb_readonly()
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

    @app.get("/intersections", response_model=IntersectionListResponse, response_model_exclude_none=True)
    def list_intersections(
        request: Request,
        bottleneck_only: bool = False,
    ) -> IntersectionListResponse:
        items = request.app.state.repository.list_latest(bottleneck_only=bottleneck_only)
        return IntersectionListResponse(count=len(items), items=items)

    @app.get(
        "/intersections/{intersection_id}",
        response_model=IntersectionStatus,
        response_model_exclude_none=True,
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

    _mount_ui(app)
    return app


app = create_app()
