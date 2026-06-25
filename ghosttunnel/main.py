from __future__ import annotations

import structlog
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from .api.admin_interface import create_admin_router
from .api.dashboard import create_dashboard_router
from .api.endpoints import router as api_router
from .integration.mutantshield import MutantShieldIntegration, create_mutantshield_router
from .core.stealth_engine import GhostTunnelEngine
from .settings import get_settings

load_dotenv()

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    cfg = settings.as_engine_dict()
    engine = GhostTunnelEngine(cfg)
    await engine.start()
    app.state.engine = engine
    log.info(
        "ghosttunnel.config",
        fast_ack=settings.ghosttunnel_fast_ack,
        quantum_buffer_min=settings.entropy_buffer_min_bytes,
    )
    ms = MutantShieldIntegration(cfg)
    app.state.mutantshield = ms
    await ms.start_webhook_server(engine)
    log.info("ghosttunnel.started", port=settings.api_port)
    yield
    await ms.stop_webhook_server()
    await engine.stop()
    log.info("ghosttunnel.stopped")


app = FastAPI(title="GhostTunnel", version="0.1.0", lifespan=lifespan)


def _get_engine():
    return app.state.engine


app.include_router(api_router)
app.include_router(create_admin_router())
app.include_router(create_mutantshield_router(get_settings().as_engine_dict(), _get_engine))
app.include_router(create_dashboard_router(_get_engine))

try:
    from prometheus_client import make_asgi_app

    app.mount("/metrics", make_asgi_app())
except Exception:
    pass

