from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class NetworkContext(BaseModel):
    flow_id: str
    src_ip: str
    dst_ip: str


class DetectionContext(BaseModel):
    risk_score: float
    risk_label: str
    is_attack: bool
    attack_family: str
    confidence_band: str
    model_consensus: str


class AuthContext(BaseModel):
    verified: bool = False
    token: Optional[str] = None
    timestamp: Optional[float] = None
    trust_level: Optional[str] = None
    status: str = Field(default="pending", description="pending|ok|failed")
    reason: Optional[str] = None


class EthicsContext(BaseModel):
    decision: Optional[str] = None
    confidence: Optional[float] = None
    requires_human_review: bool = False
    reason: Optional[str] = None


class ActionContext(BaseModel):
    final_action: str = Field(default="investigate")
    executed: bool = False
    reason: Optional[str] = None
    transmit_job_id: Optional[str] = None
    transmit_status: Optional[str] = None
    ghosttunnel_assurance_state: Optional[str] = None


class AuditContext(BaseModel):
    logged: bool = False
    ledger_event_id: Optional[str] = None
    reason: Optional[str] = None


class PipelineTimingsMs(BaseModel):
    """Per-component latency breakdown (milliseconds)."""

    qauth_ms: float = 0.0
    ethicq_ms: float = 0.0
    chronoledger_ms: float = 0.0
    ghosttunnel_ms: float = 0.0
    total_ms: float = 0.0
    oracle_overhead_ms: float = 0.0
    retry_count: int = 0
    retry_service: Optional[str] = None
    retry_reason: Optional[str] = None


class AssuranceStates(BaseModel):
    qauth_entropy_source: str = "unknown"
    qauth_assurance_state: str = "unknown"
    ethicq_provenance_state: str = "unknown"
    chronoledger_assurance_state: str = "unknown"
    ghosttunnel_entropy_source: str = "unknown"
    ghosttunnel_assurance_state: str = "unknown"


class OracleEvent(BaseModel):
    """Canonical event representation as it moves through Oracle Core."""

    oracle_trace_id: str
    status: str = Field(default="ok", description="ok|degraded")
    failed_services: list[str] = Field(default_factory=list)
    timestamp: float
    network: NetworkContext
    detection: DetectionContext
    auth: AuthContext
    ethics: EthicsContext
    action: ActionContext
    audit: AuditContext
    pipeline_timings_ms: Optional[PipelineTimingsMs] = None
    assurance_states: Optional[AssuranceStates] = None

