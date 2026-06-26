import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { Button } from "@/app/components/ui/button";
import {
  Shield,
  Clock,
  Scale,
  Radio,
  Lock,
  AlertTriangle,
  TrendingUp,
  Activity,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { SystemWarnings } from "@/app/components/system-warnings";
import { ReportLinks } from "@/app/components/report-links";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { API_BASE, fetchLatestEvents, runBackendValidation, runHealthCheck } from "@/app/lib/api";

const moduleIcons: Record<string, typeof Shield> = {
  mutantshield: Shield,
  chronoledger: Clock,
  ethicq: Scale,
  ghosttunnel: Radio,
  qauthcore: Lock,
  oracle_core: Activity,
};

const moduleLabels: Record<string, string> = {
  mutantshield: "MutantShield",
  chronoledger: "ChronoLedger",
  ethicq: "EthicQ",
  ghosttunnel: "GhostTunnel",
  qauthcore: "QAuthCore",
  oracle_core: "Oracle Core",
};

function SourceLabel({ source }: { source: "LIVE" | "REPORT" | "REPORT DATA" | "DEMO" | "DEMO VISUAL" | "LIVE/REPORT" }) {
  const color =
    source === "LIVE"
      ? "text-[#00ffcc] border-[#00ffcc]/30 bg-[#00ffcc]/10"
      : source === "REPORT" || source === "REPORT DATA"
        ? "text-[#00d4ff] border-[#00d4ff]/30 bg-[#00d4ff]/10"
        : source === "LIVE/REPORT"
          ? "text-[#fbbf24] border-[#fbbf24]/30 bg-[#fbbf24]/10"
          : "text-gray-400 border-white/10 bg-white/5";
  return (
    <span className={`ml-2 px-2 py-0.5 rounded border text-[10px] uppercase tracking-wider ${color}`}>
      {source}
    </span>
  );
}

type LatestEvent = {
  timestamp?: number | string | null;
  oracle_trace_id?: string | null;
  flow_id?: string | null;
  risk_label?: string | null;
  attack_family?: string | null;
  final_action?: string | null;
  audit_logged?: boolean | null;
  data_source?: string | null;
};

type ActionResult = {
  action: string;
  status: "running" | "success" | "failed";
  timestamp: string;
  error?: string;
  data?: Record<string, unknown> | null;
};

function fmtTime(value?: number | string | null) {
  if (value == null) return "—";
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  const ms = numeric > 10_000_000_000 ? numeric : numeric * 1000;
  return new Date(ms).toLocaleString();
}

function compactJson(value: unknown) {
  if (!value) return "No result yet.";
  return JSON.stringify(value, null, 2).slice(0, 1600);
}

export function GlobalDashboard() {
  const { data, offline, loading, refresh } = useDashboardSummary();
  const [events, setEvents] = useState<LatestEvent[]>([]);
  const [eventsError, setEventsError] = useState<string | undefined>();
  const [eventsLoading, setEventsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string>("");
  const [actionResult, setActionResult] = useState<ActionResult | null>(null);
  const summary = data;
  const perf = summary?.performance;
  const assurance = summary?.assurance;
  const ghost = summary?.ghosttunnel;
  const moduleHealth = summary?.modules || {};
  const arch = summary?.architecture_status;
  const displayWarnings = summary?.warnings || [];
  const liveReplayEvents = events.filter((event) => String(event.data_source || "").includes("LIVE_REPLAY"));
  const latestEvent = events[0];
  const auditLoggedCount = events.filter((event) => event.audit_logged === true).length;
  const isLiveConnected = !offline && summary?.backend_status === "READY";

  const successRate =
    perf?.success != null && perf.success + (perf.failed || 0) + (perf.degraded || 0) > 0
      ? ((perf.success / (perf.success + (perf.failed || 0) + (perf.degraded || 0))) * 100).toFixed(1)
      : null;

  const systemHealthPct =
    Object.values(moduleHealth).filter(Boolean).length > 0
      ? Math.round(
          (Object.values(moduleHealth).filter(Boolean).length / Object.keys(moduleHealth).length) * 100
        )
      : null;

  const refreshEvents = useCallback(async () => {
    setEventsLoading(true);
    const res = await fetchLatestEvents();
    if (res.data?.events) {
      setEvents(res.data.events as LatestEvent[]);
      setEventsError(undefined);
    } else {
      setEventsError(res.error || "Unable to load latest events");
    }
    setEventsLoading(false);
    return res;
  }, []);

  const refreshAll = useCallback(async () => {
    const [summaryRes, eventsRes] = await Promise.all([refresh(), refreshEvents()]);
    setLastRefresh(new Date().toLocaleString());
    if (summaryRes.error || eventsRes.error) {
      setActionResult({
        action: "Refresh",
        status: "failed",
        timestamp: new Date().toLocaleString(),
        error: summaryRes.error || eventsRes.error,
      });
    } else {
      setActionResult({
        action: "Refresh",
        status: "success",
        timestamp: new Date().toLocaleString(),
        data: {
          backend_status: summaryRes.data?.backend_status,
          latest_events: eventsRes.data?.events?.length ?? 0,
        },
      });
    }
  }, [refresh, refreshEvents]);

  const runAction = useCallback(
    async (action: string, fn: () => Promise<{ data: Record<string, unknown> | null; error?: string }>) => {
      const started = new Date().toLocaleString();
      setActionResult({ action, status: "running", timestamp: started });
      const res = await fn();
      setActionResult({
        action,
        status: res.error ? "failed" : "success",
        timestamp: new Date().toLocaleString(),
        error: res.error,
        data: res.data,
      });
      await refreshAll();
    },
    [refreshAll],
  );

  useEffect(() => {
    refreshEvents().then(() => setLastRefresh(new Date().toLocaleString()));
  }, [refreshEvents]);

  const actionStatusClass = useMemo(() => {
    if (!actionResult) return "border-white/10 text-gray-400";
    if (actionResult.status === "success") return "border-[#00ffcc]/30 text-[#00ffcc]";
    if (actionResult.status === "failed") return "border-[#ff3366]/30 text-[#ff3366]";
    return "border-[#fbbf24]/30 text-[#fbbf24]";
  }, [actionResult]);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl mb-1">Global Dashboard</h1>
          <p className="text-sm text-gray-400">
            Real-time security overview and system health monitoring
          </p>
          <p className="text-xs text-gray-500 mt-1">
            API base: <code>{API_BASE}</code> • Last refresh: {lastRefresh || "not refreshed yet"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-white/10" onClick={refreshAll} disabled={loading || eventsLoading}>
            <RefreshCw className={`size-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" className="border-white/10" onClick={() => runAction("Health Check", runHealthCheck)}>
            Health Check
          </Button>
          <Button variant="outline" className="border-white/10" onClick={() => runAction("Run Validation", runBackendValidation)}>
            Run Validation
          </Button>
        </div>
      </div>

      <div className={`px-4 py-3 rounded-lg border ${isLiveConnected ? "bg-[#00ffcc]/10 border-[#00ffcc]/30" : "bg-[#ff3366]/10 border-[#ff3366]/30"}`}>
        <p className={`text-sm font-semibold ${isLiveConnected ? "text-[#00ffcc]" : "text-[#ff3366]"}`}>
          Data Mode: {isLiveConnected ? "LIVE BACKEND CONNECTED" : "BACKEND OFFLINE — USING REPORT SNAPSHOT"}
        </p>
        {(eventsError || offline) && (
          <p className="text-xs text-[#ff3366] mt-1">Backend error: {eventsError || "Dashboard summary unavailable"}</p>
        )}
      </div>

      <BackendBanner offline={offline} warnings={summary?.report_warnings || []} />

      <GlassCard glow glowColor="teal">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="mb-1">Live Processing Proof <SourceLabel source="LIVE" /></h3>
              <p className="text-sm text-gray-400">Visible proof that Oracle Core is processing current event requests.</p>
            </div>
            <Button variant="outline" className="border-white/10" onClick={refreshEvents} disabled={eventsLoading}>
              <RefreshCw className={`size-4 mr-2 ${eventsLoading ? "animate-spin" : ""}`} />
              Refresh Events
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <p className="text-xs text-gray-400">Latest event count</p>
              <p className="text-xl font-semibold text-[#00ffcc]">{events.length}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 md:col-span-2">
              <p className="text-xs text-gray-400">Latest trace_id</p>
              <p className="text-sm font-mono break-all">{latestEvent?.oracle_trace_id || "—"}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <p className="text-xs text-gray-400">Latest data source</p>
              <p className="text-sm font-semibold">{latestEvent?.data_source || "—"}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <p className="text-xs text-gray-400">Audit logged</p>
              <p className="text-xl font-semibold text-[#00d4ff]">{auditLoggedCount}</p>
            </div>
          </div>
          {liveReplayEvents.length > 0 ? (
            <div className="px-4 py-3 rounded-lg bg-[#00ffcc]/10 border border-[#00ffcc]/30 text-sm text-[#00ffcc]">
              ORACLE is processing live replay events. Latest event timestamp: {fmtTime(latestEvent?.timestamp)}.
            </div>
          ) : (
            <div className="px-4 py-3 rounded-lg bg-[#fbbf24]/10 border border-[#fbbf24]/30 text-sm text-[#fbbf24]">
              No LIVE_REPLAY events visible yet. Run: <code>python scripts/oracle_realtime_replay_proof.py --events 25</code>
            </div>
          )}
        </div>
      </GlassCard>

      <GlassCard>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3>Action Result <SourceLabel source="LIVE" /></h3>
            <span className={`px-2 py-1 rounded border text-xs ${actionStatusClass}`}>
              {actionResult?.status || "idle"}
            </span>
          </div>
          <p className="text-xs text-gray-400 mb-2">
            {actionResult ? `${actionResult.action} at ${actionResult.timestamp}` : "Click Refresh, Health Check, or Run Validation to see the backend response here."}
          </p>
          {actionResult?.error && <p className="text-sm text-[#ff3366] mb-2">{actionResult.error}</p>}
          <pre className="max-h-64 overflow-auto rounded-lg bg-black/30 border border-white/10 p-3 text-xs text-gray-300">
            {compactJson(actionResult?.data)}
          </pre>
        </div>
      </GlassCard>

      <GlassCard glow glowColor="blue">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3>Latest ORACLE Events — LIVE <SourceLabel source="LIVE" /></h3>
            <Button variant="outline" className="border-white/10" onClick={refreshEvents} disabled={eventsLoading}>
              Refresh Events
            </Button>
          </div>
          {events.length === 0 ? (
            <div className="p-4 rounded-lg bg-white/5 border border-white/10 text-sm text-gray-400">
              No live events yet. Run <code>python scripts/oracle_realtime_replay_proof.py --events 25</code>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-gray-400">
                  <tr className="border-b border-white/10">
                    <th className="text-left py-2 pr-3">timestamp</th>
                    <th className="text-left py-2 pr-3">oracle_trace_id</th>
                    <th className="text-left py-2 pr-3">flow_id</th>
                    <th className="text-left py-2 pr-3">risk_label</th>
                    <th className="text-left py-2 pr-3">attack_family</th>
                    <th className="text-left py-2 pr-3">final_action</th>
                    <th className="text-left py-2 pr-3">audit_logged</th>
                    <th className="text-left py-2">data_source</th>
                  </tr>
                </thead>
                <tbody>
                  {events.slice(0, 10).map((event, idx) => {
                    const liveReplay = String(event.data_source || "").includes("LIVE_REPLAY");
                    return (
                      <tr key={`${event.oracle_trace_id || event.flow_id || idx}`} className="border-b border-white/5">
                        <td className="py-2 pr-3 whitespace-nowrap">{fmtTime(event.timestamp)}</td>
                        <td className="py-2 pr-3 font-mono max-w-[220px] truncate">{event.oracle_trace_id || "—"}</td>
                        <td className="py-2 pr-3 font-mono max-w-[180px] truncate">{event.flow_id || "—"}</td>
                        <td className="py-2 pr-3">{event.risk_label || "—"}</td>
                        <td className="py-2 pr-3">{event.attack_family || "—"}</td>
                        <td className="py-2 pr-3">{event.final_action || "—"}</td>
                        <td className="py-2 pr-3">{event.audit_logged === true ? "true" : event.audit_logged === false ? "false" : "—"}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded border ${liveReplay ? "text-[#00ffcc] border-[#00ffcc]/30 bg-[#00ffcc]/10" : "text-[#00d4ff] border-[#00d4ff]/30 bg-[#00d4ff]/10"}`}>
                            {event.data_source || "REPORT"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </GlassCard>

      <GlassCard glow glowColor="blue">
        <div className="p-6">
          <h3 className="mb-4 text-sm uppercase tracking-wider text-gray-400">
            Architecture Status <SourceLabel source="LIVE" />
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-gray-400 mb-1">Backend</p>
              <StatusBadge status={arch?.backend_ready ? "READY" : summary?.backend_status} />
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-gray-400 mb-1">Async Quantum Assurance</p>
              <StatusBadge status={arch?.async_quantum_assurance_active ? "ACTIVE" : "OFF"} />
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-gray-400 mb-1">GhostTunnel Fast-Ack</p>
              <StatusBadge status={arch?.ghosttunnel_fast_ack_active ? "ACTIVE" : "OFF"} />
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-gray-400 mb-1">Evolution</p>
              <StatusBadge status={arch?.evolution_ready || arch?.evolution_dry_run_pass ? "READY" : "FAIL"} />
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-gray-400 mb-1">Promotion</p>
              <StatusBadge status={arch?.promotion_blocked_safe ? "BLOCKED_SAFE" : "UNSAFE"} />
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard>
        <div className="p-6">
          <SystemWarnings warnings={displayWarnings} />
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard glow glowColor="blue">
          <div className="p-6">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Avg Latency <SourceLabel source="REPORT DATA" /></p>
            <p className="text-3xl font-semibold text-[#00d4ff]">
              {perf?.avg_latency_ms != null ? `${perf.avg_latency_ms.toFixed(1)}ms` : "—"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              P95: {perf?.p95_latency_ms != null ? `${perf.p95_latency_ms.toFixed(1)}ms` : "—"}
            </p>
          </div>
        </GlassCard>
        <GlassCard glow glowColor="violet">
          <div className="p-6">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Pipeline Results <SourceLabel source="REPORT DATA" /></p>
            <p className="text-lg font-semibold text-[#a855f7]">
              {perf?.success ?? "—"} ok / {perf?.degraded ?? 0} degraded / {perf?.failed ?? 0} failed
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {successRate != null ? `${successRate}% success rate` : "No stress data"}
            </p>
          </div>
        </GlassCard>
        <GlassCard glow glowColor="teal">
          <div className="p-6">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">System Health <SourceLabel source="LIVE" /></p>
            <p className="text-3xl font-semibold text-[#00ffcc]">
              {systemHealthPct != null ? `${systemHealthPct}%` : "—"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {summary?.backend_status === "READY" ? "All modules nominal" : "Check warnings"}
            </p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-3 text-sm">Reports <SourceLabel source="REPORT DATA" /></h3>
            <ReportLinks />
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Assurance Pipeline <SourceLabel source="LIVE/REPORT" /></h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#00ffcc]">{assurance?.latest_completed ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Completed</p>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#fbbf24]">{assurance?.latest_pending ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Pending</p>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#ff3366]">{assurance?.latest_failed ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Failed</p>
              </div>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">GhostTunnel Jobs <SourceLabel source="LIVE/REPORT" /></h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#00ffcc]">{ghost?.jobs_completed ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Completed</p>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#fbbf24]">{ghost?.jobs_pending ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Pending</p>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <p className="text-2xl font-semibold text-[#ff3366]">{ghost?.jobs_failed ?? "—"}</p>
                <p className="text-xs text-gray-400 mt-1">Failed</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-4 text-center">
              Fast-ack: {ghost?.fast_ack_enabled ? "enabled" : "disabled"}
              {ghost?.ghosttunnel_avg_ms != null && ` • avg ${ghost.ghosttunnel_avg_ms.toFixed(1)}ms`}
            </p>
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Attack Timeline (24h) <SourceLabel source="DEMO VISUAL" /></h3>
          <div className="h-[250px] flex items-center justify-center text-gray-500 text-sm border border-dashed border-white/10 rounded-lg">
            No live timeline yet — connect Oracle Sensor stream for real-time charts
          </div>
        </div>
      </GlassCard>

      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Module Health Status <SourceLabel source="LIVE" /></h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(moduleHealth).map(([key, ok]) => {
              const Icon = moduleIcons[key] || Shield;
              const health = ok ? 100 : 0;
              return (
                <TooltipProvider key={key}>
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all cursor-pointer">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="p-2 bg-[#00d4ff]/10 rounded-lg">
                            <Icon className="size-5 text-[#00d4ff]" />
                          </div>
                          <div className={`size-2 rounded-full ${ok ? "bg-[#00ffcc] animate-pulse" : "bg-[#ff3366]"}`} />
                        </div>
                        <p className="text-xs text-gray-400 mb-1">{moduleLabels[key] || key}</p>
                        <p className={`text-lg font-semibold ${ok ? "text-[#00ffcc]" : "text-[#ff3366]"}`}>
                          {ok ? "Active" : "Offline"}
                        </p>
                        <div className="w-full h-1.5 bg-white/5 rounded-full mt-2 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-[#00d4ff] to-[#00ffcc] rounded-full"
                            style={{ width: `${health}%` }}
                          />
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{moduleLabels[key]}: {ok ? "Healthy" : "Unavailable"}</p>
                    </TooltipContent>
                  </UITooltip>
                </TooltipProvider>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {summary?.evolution && (
        <GlassCard glow glowColor="violet">
          <div className="p-6 flex items-start gap-3">
            <AlertTriangle className="size-5 text-[#fbbf24] mt-0.5 shrink-0" />
            <div>
              <h3 className="mb-2">Evolution Engine <SourceLabel source="REPORT DATA" /></h3>
              <p className="text-sm text-gray-400">
                Status: <StatusBadge status={summary.evolution.final_status} /> • Promotion:{" "}
                <StatusBadge status={summary.evolution.promotion_status} />
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Candidate: {summary.evolution.candidate_id || "none"} • GAN: {summary.evolution.gan_status} • ART:{" "}
                {summary.evolution.art_status}
              </p>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
