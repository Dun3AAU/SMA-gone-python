import asyncio
import hmac
import os
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.service import MarketService, ROOT_DIR


class SaleRequest(BaseModel):
    beer_code: str = Field(min_length=1, max_length=12)
    request_id: UUID


class SimulationRequest(BaseModel):
    enabled: bool
    sales_per_minute: float = Field(default=4, ge=0, le=1000)
    seed: int = 1
    noise_percent: float = Field(default=0, ge=0, le=100)


def create_app(service: MarketService | None = None) -> FastAPI:
    market = service or MarketService(
        database_path=os.environ.get("MARKET_DATABASE", str(ROOT_DIR / "data" / "market.sqlite3")),
        noise_percent=(
            float(os.environ["MARKET_NOISE_PERCENT"])
            if "MARKET_NOISE_PERCENT" in os.environ
            else None
        ),
    )
    admin_token = os.environ.get("MARKET_ADMIN_TOKEN", "")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async def interval_worker() -> None:
            while True:
                market.state()
                await asyncio.sleep(1)

        worker = asyncio.create_task(interval_worker())
        try:
            yield
        finally:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="Stock Market Anywhere", lifespan=lifespan)
    app.state.market = market

    @app.get("/api/state")
    def get_state() -> dict:
        return market.state()

    @app.post("/api/sales", status_code=201)
    def post_sale(sale: SaleRequest) -> dict:
        try:
            return market.record_sale(sale.beer_code, str(sale.request_id))
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown beer") from None

    @app.post("/api/admin/simulation")
    def set_simulation(
        settings: SimulationRequest,
        x_admin_token: Annotated[str | None, Header()] = None,
    ) -> dict:
        if not admin_token or not x_admin_token or not hmac.compare_digest(
            x_admin_token, admin_token
        ):
            raise HTTPException(status_code=403, detail="Admin access required")
        market.update_simulation(
            settings.enabled,
            settings.sales_per_minute,
            settings.seed,
            settings.noise_percent,
        )
        return {"ok": True}

    frontend_dir = ROOT_DIR / "frontend"

    @app.get("/", include_in_schema=False)
    def student_home() -> FileResponse:
        return FileResponse(frontend_dir / "html" / "student.html")

    @app.get("/dashboard", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(frontend_dir / "html" / "dashboard.html")

    app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
    app.mount("/images", StaticFiles(directory=frontend_dir / "images"), name="images")
    app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
    app.mount(
        "/parametres",
        StaticFiles(directory=frontend_dir / "parametres"),
        name="parametres",
    )

    return app


app = create_app()