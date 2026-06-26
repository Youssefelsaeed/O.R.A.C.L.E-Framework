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
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { SystemWarnings } from "@/app/components/system-warnings";
import { ReportLinks } from "@/app/components/report-links";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { runBackendValidation, runHealthCheck } from "@/app/lib/api";

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

function SourceLabel({ source }: { source: "LIVE" | "REPORT" | "DEMO" | "LIVE/REPORT" }) {
  const color =
    source === "LIVE"
      ? "text-[#00ffcc] border-[#00ffcc]/30 bg-[#00ffcc]/10"
      : source === "REPORT"
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

export function GlobalDashboard() {
  const { data, offline, loading, refresh } = useDashboardSummary();
  const summary = data;
  const perf = summary?.performance;
  const assurance = summary?.assurance;
  const ghost = summary?.ghosttunnel;
  const moduleHealth = summary?.modules || {};
  const arch = summary?.architecture_status;
  const displayWarnings = summary?.warnings || [];

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

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">Global Dashboard</h1>
          <p className="text-sm text-gray-400">
            Real-time security overview and system health monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-white/10" onClick={() => refresh()} disabled={loading}>
            <RefreshCw className={`size-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" className="border-white/10" onClick={() => runHealthCheck()}>
            Health Check
          </Button>
          <Button variant="outline" className="border-white/10" onClick={() => runBackendValidation()}>
            Run Validation
          </Button>
        </div>
      </div>

      <BackendBanner offline={offline} />

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
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Avg Latency <SourceLabel source="REPORT" /></p>
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
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Pipeline Results <SourceLabel source="REPORT" /></p>
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
            <h3 className="mb-3 text-sm">Reports <SourceLabel source="REPORT" /></h3>
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
          <h3 className="mb-4">Attack Timeline (24h) <SourceLabel source="DEMO" /></h3>
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
              <h3 className="mb-2">Evolution Engine <SourceLabel source="REPORT" /></h3>
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
