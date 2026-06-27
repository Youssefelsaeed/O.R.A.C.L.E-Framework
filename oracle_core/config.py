from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OracleCoreSettings(BaseSettings):
    """Environment-driven settings for Oracle Core orchestrator."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    qauthcore_url: AnyHttpUrl = Field(
        default="http://localhost:8001",
        description="Base URL for Q-AuthCore API",
    )
    ethicq_url: AnyHttpUrl = Field(
        default="http://localhost:8002",
        description="Base URL for EthicQ API",
    )
    chronoledger_url: AnyHttpUrl = Field(
        default="http://localhost:8003",
        description="Base URL for ChronoLedger API",
    )
    ghosttunnel_url: AnyHttpUrl = Field(
        default="http://localhost:8004",
        description="Base URL for GhostTunnel API",
    )

    request_timeout_seconds: float = Field(
        default=10.0,
        description="Default HTTP timeout for downstream calls.",
    )
    oracle_async_assurance: bool = Field(
        default=True,
        description="Enable deferred async assurance pipeline while keeping sync mode available.",
    )
    oracle_token_cache_ttl_seconds: float = Field(
        default=0.0,
        description="Optional short-lived verified QAuth token cache for high-throughput operator validation.",
    )


@lru_cache
def get_settings() -> OracleCoreSettings:
    return OracleCoreSettings()

