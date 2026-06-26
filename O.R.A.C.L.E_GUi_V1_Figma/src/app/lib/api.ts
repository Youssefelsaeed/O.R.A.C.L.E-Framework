export const API_BASE =
  import.meta.env.VITE_ORACLE_API_BASE_URL || "http://127.0.0.1:8000";

export type BackendStatus = "READY" | "DEGRADED" | "UNKNOWN";

export interface DashboardSummary {
  backend_status: BackendStatus;
  modules: Record<string, boolean>;
  performance: {
    avg_latency_ms?: number | null;
    p95_latency_ms?: number | null;
    max_latency_ms?: number | null;
    success?: number | null;
    degraded?: number | null;
    failed?: number | null;
  };
  assurance: {
    latest_completed?: number | null;
    latest_pending?: number | null;
    latest_failed?: number | null;
    async_assurance_enabled?: boolean;
  };
  ghosttunnel: {
    jobs_completed?: number | null;
    jobs_pending?: number | null;
    jobs_failed?: number | null;
    fast_ack_enabled?: boolean;
    avg_latency_ms?: number | null;
    ghosttunnel_avg_ms?: number | null;
  };
  evolution: EvolutionSummary;
  chronoledger_evidence: ChronoSummary;
  warnings: string[];
  report_warnings?: string[];
  architecture_status?: {
    backend_ready?: boolean;
    async_quantum_assurance_active?: boolean;
    ghosttunnel_fast_ack_active?: boolean;
    evolution_dry_run_pass?: boolean;
    evolution_ready?: boolean;
    promotion_blocked_safe?: boolean;
  };
  gui_alignment?: {
    evolution_engine_title?: string;
    evolution_engine_subtitle?: string;
    safety_controls_disabled?: string[];
  };
}

export interface EvolutionSummary {
  final_status?: string | null;
  dry_run?: boolean;
  candidate_trained?: boolean;
  candidate_id?: string | null;
  evaluation_passed?: boolean;
  promotion_allowed?: boolean;
  promotion_status?: string | null;
  baseline_quality_warning?: boolean;
  gan_status?: string | null;
  art_status?: string | null;
  promoted?: boolean;
  promotion_simulated?: boolean;
  datasets_used?: string[];
  supervised_buffer_count?: number | null;
  anomaly_buffer_count?: number | null;
  unverified_buffer_count?: number | null;
  adversarial_samples_generated?: number | null;
  evaluation_reasons?: string[];
  schema_compatible?: boolean;
  baseline_present?: boolean;
}

export interface ChronoSummary {
  total_events?: number;
  bucket_counts?: Record<string, number>;
  unverified_count?: number;
  require_human_approval?: boolean;
  false_positive_candidate?: number;
  outlier_candidate?: number;
}

export interface ApiResult<T> {
  data: T | null;
  offline: boolean;
  error?: string;
  status?: number;
}

let lastKnownSummary: DashboardSummary | null = null;

async function apiFetch<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
    const text = await res.text();
    let data: T | null = null;
    try {
      data = text ? (JSON.parse(text) as T) : null;
    } catch {
      data = null;
    }
    if (!res.ok) {
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as Record<string, unknown>).detail)
          : text.slice(0, 300);
      return { data: null, offline: false, status: res.status, error: `HTTP ${res.status}${detail ? `: ${detail}` : ""}` };
    }
    return { data, offline: false, status: res.status };
  } catch (error) {
    return {
      data: null,
      offline: true,
      error: error instanceof Error ? `Backend Offline: ${error.message}` : "Backend Offline",
    };
  }
}

export function getLastKnownSummary(): DashboardSummary | null {
  return lastKnownSummary;
}

export async function fetchDashboardSummary(): Promise<ApiResult<DashboardSummary>> {
  const result = await apiFetch<DashboardSummary>("/oracle/dashboard/summary");
  if (result.data) lastKnownSummary = result.data;
  else if (lastKnownSummary && result.offline) {
    return { data: lastKnownSummary, offline: true, error: result.error };
  }
  return result;
}

export async function fetchHealth() {
  return apiFetch<{
    backend_status: BackendStatus;
    modules: Record<string, boolean>;
    warnings: string[];
  }>("/oracle/dashboard/health");
}

export async function fetchPerformance() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/performance");
}

export async function fetchEvolution() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/evolution");
}

export async function fetchChronoEvidence() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/chronoledger-evidence");
}

export async function fetchLatestEvents() {
  return apiFetch<{ events: Record<string, unknown>[]; warnings?: string[] }>("/oracle/dashboard/latest-events");
}

export async function runHealthCheck() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/actions/health-check", {
    method: "POST",
  });
}

export async function runBackendValidation() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/actions/backend-validation", {
    method: "POST",
  });
}

export async function runEvolutionDryRun() {
  return apiFetch<Record<string, unknown>>("/oracle/dashboard/actions/evolution-dry-run", {
    method: "POST",
  });
}

export const SAFETY_BLOCKED_MSG = "Blocked by ORACLE safety policy.";

export function isPromotionBlocked(summary?: EvolutionSummary | null): boolean {
  if (!summary) return true;
  return !summary.promotion_allowed || summary.baseline_quality_warning === true;
}
