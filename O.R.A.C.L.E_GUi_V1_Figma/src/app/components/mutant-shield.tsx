import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { ModuleModeCard } from "@/app/components/module-mode-card";
import { DataBadge, useOperatorActionPanel } from "@/app/components/operator-action-panel";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { fetchModuleStatus, runEvolutionDryRun } from "@/app/lib/api";
import { useEffect, useState } from "react";
import {
  Brain,
  Network,
  Activity,
  Zap,
  GitBranch,
  Play,
  Eye,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const models = [
  {
    name: "XGBoost Classifier",
    icon: Brain,
    status: "active",
    confidence: 94.2,
    detectionRate: 98.1,
    color: "#00d4ff",
    description: "Gradient boosting for attack pattern classification",
  },
  {
    name: "Autoencoder",
    icon: Network,
    status: "active",
    confidence: 89.7,
    detectionRate: 95.3,
    color: "#00ffcc",
    description: "Anomaly detection through reconstruction error",
  },
  {
    name: "LSTM Network",
    icon: Activity,
    status: "training",
    confidence: 91.5,
    detectionRate: 96.8,
    color: "#a855f7",
    description: "Sequential pattern analysis and prediction",
  },
  {
    name: "Graph Neural Network",
    icon: GitBranch,
    status: "active",
    confidence: 87.3,
    detectionRate: 93.4,
    color: "#fbbf24",
    description: "Network topology-based threat detection",
  },
  {
    name: "Generative Adversarial Network",
    icon: Zap,
    status: "idle",
    confidence: 85.6,
    detectionRate: 91.2,
    color: "#ff9500",
    description: "Adversarial training for robust detection",
  },
];

const anomalyStream = [
  { timestamp: "14:23:15", severity: "high", type: "Port Scan", ip: "192.168.1.45" },
  { timestamp: "14:23:42", severity: "medium", type: "SQL Injection", ip: "10.0.34.122" },
  { timestamp: "14:24:01", severity: "low", type: "Rate Limit", ip: "172.16.0.88" },
  { timestamp: "14:24:18", severity: "critical", type: "DDoS Pattern", ip: "203.0.113.42" },
  { timestamp: "14:24:35", severity: "medium", type: "Brute Force", ip: "198.51.100.17" },
];

const detectionHistory = [
  { time: "00:00", rate: 94 },
  { time: "04:00", rate: 96 },
  { time: "08:00", rate: 93 },
  { time: "12:00", rate: 97 },
  { time: "16:00", rate: 95 },
  { time: "20:00", rate: 98 },
  { time: "23:59", rate: 96 },
];

export function MutantShield() {
  const { data, offline, refresh } = useDashboardSummary();
  const action = useOperatorActionPanel();
  const [moduleStatus, setModuleStatus] = useState<Record<string, unknown> | null>(null);
  const evo = data?.evolution;
  const bufferCount = evo?.supervised_buffer_count;

  useEffect(() => {
    fetchModuleStatus().then((response) => setModuleStatus(response.data));
  }, []);

  const monitoring = (moduleStatus?.monitoring || {}) as Record<string, unknown>;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">MutantShield</h1>
          <p className="text-sm text-gray-400">
            FusionEngineV2 production • Evolution Engine dry-run only
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            className="border-[#ff3366]/30 text-[#ff3366]"
            onClick={() =>
              action.showLocked(
                "Trigger Retraining",
                "Production retraining is blocked. Use Evolution Dry-Run / candidate-only mode.",
                { production_models_unchanged: true, allowed_action: "POST /oracle/dashboard/actions/evolution-dry-run" },
              )
            }
          >
            <Play className="size-4 mr-2" />
            Trigger Retraining
          </Button>
          <Button
            className="bg-[#00d4ff] hover:bg-[#00d4ff]/90 text-black"
            onClick={() => action.runAction("Run Evolution Dry-Run", async () => {
              const result = await runEvolutionDryRun();
              await refresh();
              return result;
            })}
          >
            <TrendingUp className="size-4 mr-2" />
            Run Evolution Dry-Run
          </Button>
        </div>
      </div>

      <BackendBanner offline={offline} />
      {action.Panel}

      <ModuleModeCard
        title="MutantShield"
        lines={[
          "Production FusionEngineV2 active",
          "Evolution Engine available",
          "Promotion blocked until fair baseline",
        ]}
      />

      <GlassCard>
        <div className="p-5">
          <h3 className="mb-3">Monitoring Mode <DataBadge label="LIVE/REPORT" /></h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div><p className="text-gray-400 text-xs">Live Network Capture</p><p className="font-semibold">{String(monitoring.live_network_capture || "NOT_ACTIVE")}</p></div>
            <div><p className="text-gray-400 text-xs">Realtime Replay</p><p className="font-semibold">{String(monitoring.realtime_replay || "UNKNOWN")}</p></div>
            <div><p className="text-gray-400 text-xs">Latest Event Source</p><p className="font-semibold">{String(monitoring.latest_event_source || "REPORT")}</p></div>
            <div><p className="text-gray-400 text-xs">Last Trace ID</p><p className="font-mono text-xs break-all">{String(monitoring.last_trace_id || "—")}</p></div>
            <div><p className="text-gray-400 text-xs">Last Event Timestamp</p><p>{String(monitoring.last_event_timestamp || "—")}</p></div>
            <div><p className="text-gray-400 text-xs">Next Command</p><code className="text-xs">python scripts/oracle_realtime_replay_proof.py --events 25</code></div>
          </div>
          <p className="text-xs text-[#fbbf24] mt-3">
            Live network capture is not active unless live sensor readiness passes. Realtime replay proof is available and validated.
          </p>
        </div>
      </GlassCard>

      <GlassCard glow glowColor="violet">
        <div className="p-6 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="size-5 text-[#fbbf24] shrink-0 mt-0.5" />
            <p className="text-sm text-[#fbbf24]">
              Production model promotion is blocked until fair baseline validation passes.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-400 text-xs">FusionEngine</p>
              <StatusBadge status={data?.backend_status === "READY" ? "ACTIVE" : "UNKNOWN"} />
            </div>
            <div>
              <p className="text-gray-400 text-xs">Training Buffer</p>
              <p className="font-semibold">{bufferCount ?? "—"} samples</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Candidate</p>
              <p className="font-semibold text-xs truncate">{evo?.candidate_id || "none"}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Promotion</p>
              <StatusBadge status={evo?.promotion_status} />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <p>Datasets: {(evo?.datasets_used || ["CIC-IDS2017", "UNSW-NB15"]).join(", ")}</p>
            <p>Candidate trained: {evo?.candidate_trained ? "true" : "false"}</p>
            <p>Evaluation passed: {evo?.evaluation_passed ? "true" : "false"}</p>
            <p>Promotion allowed: {evo?.promotion_allowed ? "true" : "false"}</p>
          </div>
        </div>
      </GlassCard>

      {/* AI Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {models.map((model) => {
          const Icon = model.icon;
          const statusColors = {
            active: "bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30",
            training: "bg-[#fbbf24]/10 text-[#fbbf24] border-[#fbbf24]/30",
            idle: "bg-gray-500/10 text-gray-400 border-gray-500/30",
          };

          return (
            <GlassCard key={model.name} className="hover:border-[#00d4ff]/30 transition-all">
              <div className="p-5">
                <DataBadge label="REPORT" />
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="p-3 rounded-lg"
                    style={{ backgroundColor: `${model.color}15` }}
                  >
                    <Icon className="size-6" style={{ color: model.color }} />
                  </div>
                  <Badge
                    className={`${
                      statusColors[model.status as keyof typeof statusColors]
                    } border text-xs uppercase`}
                    variant="outline"
                  >
                    {model.status}
                  </Badge>
                </div>

                <h3 className="mb-2">{model.name}</h3>
                <p className="text-xs text-gray-400 mb-4">{model.description}</p>

                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">Confidence</span>
                      <span className="text-xs font-semibold" style={{ color: model.color }}>
                        {model.confidence}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${model.confidence}%`,
                          backgroundColor: model.color,
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">Detection Rate</span>
                      <span className="text-xs font-semibold" style={{ color: model.color }}>
                        {model.detectionRate}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${model.detectionRate}%`,
                          backgroundColor: model.color,
                        }}
                      />
                    </div>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-4 border-white/10 hover:border-[#00d4ff]/50"
                >
                  <Eye className="size-4 mr-2" />
                  View Model Details
                </Button>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* Detection History Chart & Live Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detection Rate History */}
        <GlassCard className="lg:col-span-2">
          <div className="p-6">
            <h3 className="mb-4">Detection Rate History (24h)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={detectionHistory}>
                <defs>
                  <linearGradient id="detectionGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#00d4ff" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time" stroke="#666" style={{ fontSize: "12px" }} />
                <YAxis
                  domain={[85, 100]}
                  stroke="#666"
                  style={{ fontSize: "12px" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#12121a",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="url(#detectionGradient)"
                  strokeWidth={3}
                  dot={{ fill: "#00d4ff", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Live Anomaly Stream */}
        <GlassCard>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
                  <h3>Live Anomaly Stream <DataBadge label="DEMO" /></h3>
              <div className="flex items-center gap-2">
                <div className="size-2 bg-[#00ffcc] rounded-full animate-pulse" />
                <span className="text-xs text-gray-400">Live</span>
              </div>
            </div>

            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {anomalyStream.map((event, idx) => {
                const severityColors = {
                  critical: "bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30",
                  high: "bg-[#ff9500]/10 text-[#ff9500] border-[#ff9500]/30",
                  medium: "bg-[#fbbf24]/10 text-[#fbbf24] border-[#fbbf24]/30",
                  low: "bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30",
                };

                return (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <Badge
                        className={`${
                          severityColors[event.severity as keyof typeof severityColors]
                        } border text-xs uppercase`}
                        variant="outline"
                      >
                        {event.severity}
                      </Badge>
                      <span className="text-xs text-gray-500">{event.timestamp}</span>
                    </div>
                    <p className="text-xs font-semibold mb-1">{event.type}</p>
                    <p className="text-xs text-gray-400">Source: {event.ip}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Dataset Lineage */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Dataset Lineage & Training Pipeline</h3>
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            {[
              "Raw Traffic Data",
              "Feature Engineering",
              "Data Augmentation",
              "Model Training",
              "Validation",
            ].map((step, idx) => (
              <div key={idx} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className="size-12 rounded-full bg-gradient-to-br from-[#00d4ff] to-[#a855f7] flex items-center justify-center shadow-[0_0_20px_rgba(0,212,255,0.3)]">
                    <span className="text-sm font-semibold">{idx + 1}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2 text-center max-w-[100px]">
                    {step}
                  </p>
                </div>
                {idx < 4 && (
                  <div className="w-16 h-0.5 bg-gradient-to-r from-[#00d4ff] to-[#a855f7] mx-2" />
                )}
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
