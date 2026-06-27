from __future__ import annotations

print("REAL ORACLE CORE FILE LOADED", __file__)

import time
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.dashboard import router as dashboard_router
from .config import get_settings
from .models.oracle_event import OracleEvent
from .orchestrator import OracleOrchestrator
from .payload_validation import validate_oracle_payload

STARTED_AT = time.time()
CODE_MARKER = "phase12_18b_runtime"


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.getcwd(),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        app.state.http_client = client
        yield


app = FastAPI(
    title="Oracle Core Orchestrator",
    description="Central orchestrator for Project O.R.A.C.L.E.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)


@app.get("/health", summary="Oracle Core service health.")
async def health() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "oracle_core",
        "code_marker": CODE_MARKER,
        "token_cache_ttl_seconds": settings.oracle_token_cache_ttl_seconds,
        "downstream": {
            "qauthcore_url": str(settings.qauthcore_url),
            "ethicq_url": str(settings.ethicq_url),
            "chronoledger_url": str(settings.chronoledger_url),
            "ghosttunnel_url": str(settings.ghosttunnel_url),
        },
    }


@app.get("/oracle/runtime-info", summary="Return current Oracle Core runtime build information.")
async def runtime_info() -> Dict[str, Any]:
    return {
        "git_commit": _git_commit(),
        "app_version": app.version,
        "started_at": STARTED_AT,
        "process_id": os.getpid(),
        "code_marker": CODE_MARKER,
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
    }


def get_http_client(request: Request) -> httpx.AsyncClient:
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise RuntimeError("HTTP client not initialised on app.state")
    return client


def get_orchestrator(client: httpx.AsyncClient = Depends(get_http_client)) -> OracleOrchestrator:
    return OracleOrchestrator(client)


@app.post(
    "/oracle/process",
    response_model=OracleEvent,
    summary="Process a MutantShield detection through QAuthCore, EthicQ, and ChronoLedger.",
)
async def process_oracle_event(
    payload: Dict[str, Any],
    response: Response,
    orchestrator: OracleOrchestrator = Depends(get_orchestrator),
) -> OracleEvent:
    """
    Orchestrate the full Oracle pipeline for a single MutantShield-style event.

    Input: raw JSON from MutantShield (flow_id, src_ip, dst_ip, risk_* fields, etc.).
    Output: fully populated OracleEvent document.
    """
    if len(str(payload)) > 100_000:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "status": "rejected",
                "reason": "payload_too_large",
                "details": ["payload exceeds 100000 character safety limit"],
            },
        )

    ok, details = validate_oracle_payload(payload)
    if not ok:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "rejected",
                "reason": "invalid_payload",
                "details": details,
            },
        )

    try:
        result = await orchestrator.process_mutantshield_event(payload)
        if result.status == "degraded":
            response.status_code = status.HTTP_207_MULTI_STATUS
        return result
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "rejected",
                "reason": "invalid_payload",
                "details": [str(exc)],
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"oracle_pipeline_failed:{exc!s}",
        ) from exc


@app.get("/oracle/test", summary="Return a sample MutantShield-style input payload for quick testing.")
async def oracle_test_input() -> JSONResponse:
    sample = {
        "flow_id": "flow-test-1",
        "risk_score": 0.92,
        "risk_label": "HIGH",
        "is_attack": True,
        "attack_family": "DDoS",
        "src_ip": "192.168.1.10",
        "dst_ip": "10.0.0.5",
        "confidence_band": "HIGH",
        "model_consensus": "3/4",
        "timestamp": time.time(),
    }
    return JSONResponse(content=sample)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("oracle_core.main:app", host="0.0.0.0", port=8010, reload=False)

