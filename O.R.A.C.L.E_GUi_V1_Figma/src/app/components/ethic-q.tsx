import { useState } from "react";
import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { ModuleModeCard } from "@/app/components/module-mode-card";
import { DataBadge, useOperatorActionPanel } from "@/app/components/operator-action-panel";
import { Button } from "@/app/components/ui/button";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { runHealthCheck } from "@/app/lib/api";
import { Badge } from "@/app/components/ui/badge";
import { Textarea } from "@/app/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/app/components/ui/dialog";
import {
  Scale,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Shield,
  Eye,
  Edit3,
} from "lucide-react";

const ethicsRules = [
  {
    id: 1,
    name: "Data Privacy Protection",
    description: "Prevent unauthorized access to PII and sensitive data",
    status: "active",
    violations: 0,
    actions: 124,
  },
  {
    id: 2,
    name: "Proportional Response",
    description: "Ensure defensive actions match threat severity",
    status: "active",
    violations: 2,
    actions: 89,
  },
  {
    id: 3,
    name: "Human Oversight Required",
    description: "Critical decisions require human authorization",
    status: "active",
    violations: 0,
    actions: 15,
  },
  {
    id: 4,
    name: "No Offensive Operations",
    description: "Prohibit active attacks or counter-hacking",
    status: "active",
    violations: 0,
    actions: 234,
  },
  {
    id: 5,
    name: "Transparency in AI Decisions",
    description: "All AI actions must be explainable and logged",
    status: "active",
    violations: 1,
    actions: 567,
  },
];

const recentDecisions = [
  {
    timestamp: "14:24:18",
    action: "Block IP Address",
    target: "203.0.113.42",
    verdict: "approved",
    reasoning: "DDoS pattern detected, proportional response",
    confidence: 96,
  },
  {
    timestamp: "14:19:35",
    action: "Escalate to Human",
    target: "Admin privilege request",
    verdict: "escalated",
    reasoning: "High-risk action requires human oversight",
    confidence: 99,
  },
  {
    timestamp: "14:12:47",
    action: "Data Access Request",
    target: "User records query",
    verdict: "denied",
    reasoning: "Violates data privacy protection policy",
    confidence: 100,
  },
  {
    timestamp: "14:08:22",
    action: "Rate Limit Enforcement",
    target: "API endpoint /auth",
    verdict: "approved",
    reasoning: "Proportional response to suspicious activity",
    confidence: 94,
  },
];

export function EthicQ() {
  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const { data, offline } = useDashboardSummary();
  const action = useOperatorActionPanel();
  const assurance = data?.assurance;
  const moduleOk = data?.modules?.ethicq;

  return (
    <div className="p-8 space-y-6">
      <BackendBanner offline={offline} />
      {action.Panel}
      <ModuleModeCard title="EthicQ" lines={["Provenance: cached hot path + async reconciliation"]} />
      <GlassCard>
        <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><p className="text-gray-400 text-xs">Module Health</p><StatusBadge status={moduleOk ? "ACTIVE" : "OFFLINE"} /></div>
          <div><p className="text-gray-400 text-xs">Provenance Mode</p><p>cached hot path + async</p></div>
          <div><p className="text-gray-400 text-xs">Assurance Pending</p><p className="font-semibold">{assurance?.latest_pending ?? "—"}</p></div>
          <div><p className="text-gray-400 text-xs">Assurance Failed</p><p className="font-semibold text-[#ff3366]">{assurance?.latest_failed ?? "—"}</p></div>
        </div>
      </GlassCard>
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">EthicQ</h1>
          <p className="text-sm text-gray-400">
            Ethical decision engine ensuring responsible AI operations
          </p>
        </div>
        <Button
          className="bg-[#a855f7] hover:bg-[#a855f7]/90 text-white"
          onClick={() =>
            action.showLocked(
              "Edit Rules",
              "EthicQ rule editing is locked in final demo mode. Policy changes require reviewed config update.",
              {
                locked: true,
                view_rationality_matrix: "/oracle/dashboard/reports/backend_validation",
                health_check: "POST /oracle/dashboard/actions/health-check",
              },
            )
          }
        >
          <Edit3 className="size-4 mr-2" />
          Edit Rules
        </Button>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" className="border-white/10" onClick={() => action.runAction("EthicQ Health Check", runHealthCheck)}>
          Run Health Check
        </Button>
        <a href="http://127.0.0.1:8000/oracle/dashboard/reports/backend_validation" target="_blank" rel="noreferrer">
          <Button variant="outline" className="border-white/10">View Rationality Matrix</Button>
        </a>
      </div>

      {/* Compliance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard glow glowColor="teal">
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Compliance Score <DataBadge label="REPORT" />
            </p>
            <p className="text-2xl font-semibold text-[#00ffcc]">99.2%</p>
            <p className="text-xs text-gray-500 mt-1">Excellent standing</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Active Rules <DataBadge label="REPORT" />
            </p>
            <p className="text-2xl font-semibold text-[#00d4ff]">
              {ethicsRules.length}
            </p>
            <p className="text-xs text-gray-500 mt-1">All enforced</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Decisions Today <DataBadge label="DEMO" />
            </p>
            <p className="text-2xl font-semibold text-[#a855f7]">1,029</p>
            <p className="text-xs text-gray-500 mt-1">+12% from yesterday</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Violations <DataBadge label="REPORT" />
            </p>
            <p className="text-2xl font-semibold text-[#fbbf24]">3</p>
            <p className="text-xs text-gray-500 mt-1">Reviewed & resolved</p>
          </div>
        </GlassCard>
      </div>

      {/* Ethics Rules Panel */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Active Ethics Rules <DataBadge label="REPORT" /></h3>
          <div className="space-y-3">
            {ethicsRules.map((rule) => (
              <div
                key={rule.id}
                className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-[#a855f7]/30 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Scale className="size-5 text-[#a855f7]" />
                      <h4 className="font-semibold">{rule.name}</h4>
                      <Badge className="bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30 border">
                        {rule.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">
                      {rule.description}
                    </p>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="size-4 text-[#00ffcc]" />
                        <span className="text-xs text-gray-400">
                          {rule.actions} actions enforced
                        </span>
                      </div>
                      {rule.violations > 0 && (
                        <div className="flex items-center gap-2">
                          <AlertCircle className="size-4 text-[#fbbf24]" />
                          <span className="text-xs text-[#fbbf24]">
                            {rule.violations} violation{rule.violations > 1 ? "s" : ""}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-[#00d4ff] hover:text-[#00d4ff]/80"
                    onClick={() =>
                      action.showLocked(
                        `View Rule: ${rule.name}`,
                        "Rule viewing is report-backed in this final demo. Editing production ethics policy remains locked.",
                        { data_source: "REPORT", rule: rule.name, locked_editing: true },
                      )
                    }
                  >
                    <Eye className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Decision Explanation Viewer */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Recent Ethical Decisions <DataBadge label="DEMO" /></h3>
          <div className="space-y-3">
            {recentDecisions.map((decision, idx) => {
              const verdictConfig = {
                approved: {
                  icon: CheckCircle2,
                  color: "text-[#00ffcc]",
                  bg: "bg-[#00ffcc]/10",
                  border: "border-[#00ffcc]/30",
                },
                denied: {
                  icon: XCircle,
                  color: "text-[#ff3366]",
                  bg: "bg-[#ff3366]/10",
                  border: "border-[#ff3366]/30",
                },
                escalated: {
                  icon: AlertCircle,
                  color: "text-[#fbbf24]",
                  bg: "bg-[#fbbf24]/10",
                  border: "border-[#fbbf24]/30",
                },
              };

              const config = verdictConfig[decision.verdict as keyof typeof verdictConfig];
              const Icon = config.icon;

              return (
                <div
                  key={idx}
                  className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-[#a855f7]/30 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Badge
                        className={`${config.bg} ${config.color} ${config.border} border`}
                      >
                        <Icon className="size-3 mr-1" />
                        {decision.verdict}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {decision.timestamp}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">Confidence:</span>
                      <span className="text-xs font-semibold text-[#a855f7]">
                        {decision.confidence}%
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <span className="text-xs text-gray-400">Action: </span>
                      <span className="text-sm font-semibold">
                        {decision.action}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Target: </span>
                      <span className="text-sm text-gray-300">
                        {decision.target}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5 border-l-2 border-[#a855f7]">
                      <p className="text-xs text-gray-400 mb-1">
                        Decision Reasoning:
                      </p>
                      <p className="text-sm">{decision.reasoning}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* Override Action */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="mb-1">Manual Override</h3>
              <p className="text-sm text-gray-400">
                Override an AI decision with human justification
              </p>
            </div>
            <Dialog open={overrideDialogOpen} onOpenChange={setOverrideDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-[#ff3366]/30 text-[#ff3366] hover:bg-[#ff3366]/10">
                  <Shield className="size-4 mr-2" />
                  Request Override
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#12121a] border-white/10">
                <DialogHeader>
                  <DialogTitle>Manual Override Request</DialogTitle>
                  <DialogDescription className="text-gray-400">
                    Provide justification for overriding the AI decision. This action
                    will be logged in ChronoLedger.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <label className="text-sm mb-2 block">Decision ID</label>
                    <input
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm"
                      placeholder="Enter decision ID to override"
                    />
                  </div>
                  <div>
                    <label className="text-sm mb-2 block">Justification</label>
                    <Textarea
                      className="bg-white/5 border-white/10"
                      placeholder="Explain why this override is necessary..."
                      rows={4}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setOverrideDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="bg-[#ff3366] hover:bg-[#ff3366]/90"
                    onClick={() => {
                      setOverrideDialogOpen(false);
                      action.showLocked(
                        "Submit Override",
                        "Manual override submission is simulated in final demo mode. Production policy overrides require reviewed authorization workflow.",
                        { locked: true, no_policy_change: true },
                      );
                    }}
                  >
                    Submit Override
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="p-4 rounded-lg bg-[#fbbf24]/5 border border-[#fbbf24]/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="size-5 text-[#fbbf24] mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-[#fbbf24] mb-1">
                  Critical Action Warning
                </p>
                <p className="text-xs text-gray-400">
                  Manual overrides bypass AI safety mechanisms and require
                  director-level authorization. All overrides are permanently logged
                  and audited.
                </p>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
