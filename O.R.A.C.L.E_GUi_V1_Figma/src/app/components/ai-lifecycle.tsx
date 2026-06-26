import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { ReportLinks } from "@/app/components/report-links";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { useEvolutionData } from "@/app/lib/use-oracle-data";
import { API_BASE, runEvolutionDryRun, SAFETY_BLOCKED_MSG } from "@/app/lib/api";
import { useState } from "react";
import {
  Database,
  Shield,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Play,
  Lock,
  AlertTriangle,
  Clock,
  Layers,
  Target,
  Zap,
} from "lucide-react";

const PROMOTION_BLOCKED_MSG =
  "Model promotion is blocked by ORACLE safety policy (metrics/safety gates). Candidate-only retraining and adversarial evaluation are validated; production models remain unchanged.";

function ModelCoverageRow({
  name,
  status,
  eligible,
}: {
  name: string;
  status: string;
  eligible: boolean;
}) {
  const color =
    status === "trained"
      ? "#00ffcc"
      : status === "surrogate_trained"
        ? "#fbbf24"
        : status === "not_supported" || status === "not_trained"
          ? "#ff3366"
          : "#94a3b8";
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
      <span className="text-sm">{name}</span>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="border-white/10" style={{ color }}>
          {status}
        </Badge>
        {!eligible && (
          <span className="text-xs text-gray-500">not promotion-eligible</span>
        )}
      </div>
    </div>
  );
}

function PipelineSection({
  title,
  ok,
  detail,
  icon: Icon,
}: {
  title: string;
  ok: boolean | null;
  detail: string;
  icon: typeof Database;
}) {
  const StatusIcon = ok === null ? AlertCircle : ok ? CheckCircle2 : XCircle;
  const color = ok === null ? "#fbbf24" : ok ? "#00ffcc" : "#ff3366";
  return (
    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="size-4 text-[#00d4ff]" />
        <StatusIcon className="size-4" style={{ color }} />
        <h4 className="text-sm font-semibold">{title}</h4>
      </div>
      <p className="text-xs text-gray-400">{detail}</p>
    </div>
  );
}

function EvoMetricCard({ label, value }: { label: string; value: string }) {
  return (
    <GlassCard>
      <div className="p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">{label}</p>
        <p className="text-sm font-semibold break-words">{value}</p>
      </div>
    </GlassCard>
  );
}

function SourceLabel({ source }: { source: "LIVE/CONFIG" | "REPORT" | "LIVE SAFETY POLICY" }) {
  const color =
    source === "LIVE SAFETY POLICY"
      ? "text-[#ff3366] border-[#ff3366]/30 bg-[#ff3366]/10"
      : source === "LIVE/CONFIG"
        ? "text-[#fbbf24] border-[#fbbf24]/30 bg-[#fbbf24]/10"
        : "text-[#00d4ff] border-[#00d4ff]/30 bg-[#00d4ff]/10";
  return (
    <span className={`ml-2 px-2 py-0.5 rounded border text-[10px] uppercase tracking-wider ${color}`}>
      {source}
    </span>
  );
}

export function AILifecycle() {
  const { data, offline, loading, refresh } = useEvolutionData();
  const [actionResult, setActionResult] = useState<{
    status: "idle" | "running" | "success" | "failed";
    timestamp?: string;
    error?: string;
    data?: Record<string, unknown> | null;
  }>({ status: "idle" });
  const evo = (data?.evolution || {}) as Record<string, unknown>;
  const buffer = (data?.training_buffer || {}) as Record<string, unknown>;
  const adv = (data?.adversarial_hardening || {}) as Record<string, unknown>;
  const sched = (data?.evolution_scheduler || {}) as Record<string, unknown>;
  const coverage = (data?.model_coverage || {}) as Record<string, unknown>;
  const perModel = (coverage.per_model || []) as Array<Record<string, unknown>>;
  const fullEvolutionReady = Boolean(evo.full_evolution_ready);
  const artVersion = String(evo.art_version || "—");
  const artLabel = evo.art_source === "local" ? `ART v${artVersion} local` : `ART ${artVersion}`;

  const handlePromote = () => alert(SAFETY_BLOCKED_MSG);
  const handleDryRun = async () => {
    setActionResult({ status: "running", timestamp: new Date().toLocaleString() });
    const result = await runEvolutionDryRun();
    setActionResult({
      status: result.error ? "failed" : "success",
      timestamp: new Date().toLocaleString(),
      error: result.error,
      data: result.data,
    });
    await refresh();
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">MutantShield Evolution Engine</h1>
          <p className="text-sm text-gray-400">
            Retraining, adversarial hardening, and promotion safety
          </p>
          <p className="text-xs text-gray-500 mt-1">API base: <code>{API_BASE}</code></p>
        </div>
        <div className="flex gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button className="bg-[#a855f7]/50 text-white cursor-not-allowed" disabled onClick={handlePromote}>
                    <Lock className="size-4 mr-2" />
                    Promote Candidate
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>Blocked by ORACLE safety policy.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Button
            className="bg-[#00d4ff] hover:bg-[#00d4ff]/90 text-black"
            disabled={loading}
            onClick={handleDryRun}
          >
            <Play className="size-4 mr-2" />
            Run Evolution Dry-Run
          </Button>
        </div>
      </div>

      <BackendBanner offline={offline} />

      <GlassCard>
        <div className="p-6">
          <h3 className="mb-2">Evolution Action Result <SourceLabel source="LIVE/CONFIG" /></h3>
          <p className="text-xs text-gray-400 mb-3">
            {actionResult.status === "idle"
              ? "Click Run Evolution Dry-Run to see live backend action output here."
              : `Status: ${actionResult.status} at ${actionResult.timestamp}`}
          </p>
          {actionResult.error && <p className="text-sm text-[#ff3366] mb-2">{actionResult.error}</p>}
          <pre className="max-h-64 overflow-auto rounded-lg bg-black/30 border border-white/10 p-3 text-xs text-gray-300">
            {actionResult.data ? JSON.stringify(actionResult.data, null, 2).slice(0, 1600) : "No action output yet."}
          </pre>
        </div>
      </GlassCard>

      {fullEvolutionReady && (
        <div className="px-4 py-3 rounded-lg bg-[#00ffcc]/10 border border-[#00ffcc]/30 flex items-center gap-3">
          <CheckCircle2 className="size-5 text-[#00ffcc] shrink-0" />
          <p className="text-sm font-semibold text-[#00ffcc]">FULL_EVOLUTION_READY</p>
          <span className="text-xs text-gray-400">
            Full ensemble candidate training • mandatory adversarial gate • scheduler integrated
          </span>
        </div>
      )}

      <div className="px-4 py-4 rounded-lg bg-[#ff3366]/10 border border-[#ff3366]/30 flex items-start gap-3">
        <AlertTriangle className="size-5 text-[#fbbf24] shrink-0 mt-0.5" />
          <p className="text-sm text-[#fbbf24]">
            {PROMOTION_BLOCKED_MSG} <SourceLabel source="LIVE SAFETY POLICY" />
          </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-gray-300">
          Evolution Status <SourceLabel source="REPORT" />
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <EvoMetricCard label="Framework Status" value={fullEvolutionReady ? "FULL_EVOLUTION_READY" : String(evo.final_status ?? "—")} />
          <EvoMetricCard label="Full Ensemble" value={String(evo.full_ensemble ?? true)} />
          <EvoMetricCard label="Models Trained" value={String(evo.models_trained_count ?? coverage.models_trained_count ?? "—")} />
          <EvoMetricCard label="Global Adversarial Gate" value={evo.global_adversarial_gate_passed ? "PASS" : String(evo.global_adversarial_gate_passed ?? "—")} />
          <EvoMetricCard label="Scheduler Enabled" value={String(sched.enabled ?? false)} />
          <EvoMetricCard label="Scheduler Frequency" value={String(sched.frequency ?? "—")} />
          <EvoMetricCard label="Scheduler Status" value={String(sched.status ?? "idle")} />
          <EvoMetricCard label="Human Review Queue" value={String(data?.human_review_queue_count ?? "—")} />
          <EvoMetricCard label="Candidate Trained" value={String(evo.candidate_trained ?? false)} />
          <EvoMetricCard label="Evaluation Passed" value={String(evo.evaluation_passed ?? false)} />
          <EvoMetricCard label="Promotion Allowed" value={String(evo.promotion_allowed ?? false)} />
          <EvoMetricCard label="Promotion Status" value={String(evo.promotion_status ?? "—")} />
          <EvoMetricCard label="Fair Baseline Reliable" value={String(evo.fair_baseline_reliable ?? false)} />
          <EvoMetricCard label="Baseline Quality Warning" value={String(evo.baseline_quality_warning ?? false)} />
          <EvoMetricCard label="ART Available" value={String(evo.art_available ?? false)} />
          <EvoMetricCard label="ART Version" value={artLabel} />
          <EvoMetricCard label="Attacks Run" value={((evo.attacks_run as string[]) || []).join(", ") || "—"} />
          <EvoMetricCard label="Adversarial Accuracy" value={String(evo.adversarial_accuracy ?? adv.adversarial_accuracy ?? "—")} />
          <EvoMetricCard label="Robustness Drop" value={String(evo.robustness_drop ?? adv.robustness_drop ?? "—")} />
          <EvoMetricCard label="Adversarial Training" value={String(evo.adversarial_training_enabled ?? false)} />
          <EvoMetricCard label="GAN Status" value={String(evo.gan_status ?? "—")} />
          <EvoMetricCard label="GAN Training Required" value={String(evo.gan_training_required ?? true)} />
        </div>
      </div>

      {perModel.length > 0 && (
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Full Ensemble Model Coverage <SourceLabel source="REPORT" /></h3>
            <div className="space-y-2">
              {perModel.map((m) => (
                <ModelCoverageRow
                  key={String(m.model_name)}
                  name={String(m.model_name)}
                  status={String(m.status ?? "unknown")}
                  eligible={Boolean(m.promotion_eligible)}
                />
              ))}
            </div>
          </div>
        </GlassCard>
      )}

      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Evolution Pipeline <SourceLabel source="REPORT" /></h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <PipelineSection
              title="Dataset Registry"
              icon={Database}
              ok={((evo.datasets_used as string[]) || []).length > 0}
              detail={((evo.datasets_used as string[]) || []).join(", ") || "No datasets registered"}
            />
            <PipelineSection
              title="ChronoLedger Evidence"
              icon={Clock}
              ok={(evo.unverified_buffer_count as number) != null}
              detail={`${evo.unverified_buffer_count ?? "—"} unverified • integrity-trusted, not label-trusted`}
            />
            <PipelineSection
              title="Training Buffer"
              icon={Layers}
              ok={Number(buffer.supervised_samples ?? evo.supervised_buffer_count) > 0}
              detail={`${buffer.supervised_samples ?? evo.supervised_buffer_count ?? "—"} supervised samples`}
            />
            <PipelineSection
              title="Adversarial Hardening"
              icon={Shield}
              ok={Boolean(adv.adversarial_samples_generated ?? evo.adversarial_samples_generated)}
              detail={
                adv.fallback_used || evo.art_status === "fallback"
                  ? `ART fallback${evo.art_source ? ` (source: ${evo.art_source})` : ""}`
                  : `IBM ART: ${((evo.attacks_run as string[]) || []).join(", ") || "hardening active"}`
              }
            />
            <PipelineSection
              title="GAN Adapter"
              icon={Zap}
              ok={evo.gan_status === "trained" || evo.gan_status === "available"}
              detail={
                evo.gan_training_required
                  ? `${String(evo.gan_status || "not_trained")} — train GAN later`
                  : String(evo.gan_status || "unknown")
              }
            />
            <PipelineSection
              title="Evaluation Gate"
              icon={Target}
              ok={Boolean(evo.evaluation_passed)}
              detail={String(evo.promotion_status || "pending")}
            />
            <PipelineSection
              title="Promotion Safety"
              icon={Lock}
              ok={!evo.promoted && evo.promotion_allowed === false}
              detail={`Promoted: ${String(evo.promoted ?? false)} • Simulated: ${String(evo.promotion_simulated ?? true)}`}
            />
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Training Buffer Breakdown <SourceLabel source="REPORT" /></h3>
            <div className="space-y-3">
              {Object.entries((buffer.source_counts as Record<string, number>) || {}).map(([name, count]) => (
                <div key={name} className="p-4 rounded-lg bg-white/5 border border-white/10 flex items-center justify-between">
                  <span className="text-sm">{name}</span>
                  <Badge variant="outline" className="border-white/10">{count.toLocaleString()} samples</Badge>
                </div>
              ))}
              {!buffer.source_counts && (
                <p className="text-sm text-gray-500">No training buffer report — run evolution dry-run</p>
              )}
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Evolution Reports <SourceLabel source="REPORT" /></h3>
            <ReportLinks />
          </div>
        </GlassCard>
      </div>

      {(evo.evaluation_reasons as string[])?.length > 0 && (
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Evaluation Reasons</h3>
            <ul className="space-y-1 text-sm text-gray-400">
              {(evo.evaluation_reasons as string[]).map((r) => (
                <li key={r}>• {r}</li>
              ))}
            </ul>
          </div>
        </GlassCard>
      )}

      <GlassCard>
        <div className="p-6">
          <p className="text-xs text-gray-500">Candidate ID: {String(evo.candidate_id || "none")}</p>
        </div>
      </GlassCard>
    </div>
  );
}
