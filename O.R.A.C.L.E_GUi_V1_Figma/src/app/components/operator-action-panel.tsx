import { useState } from "react";
import type { ReactNode } from "react";
import { GlassCard } from "@/app/components/glass-card";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";

type ActionStatus = "idle" | "running" | "success" | "failed" | "locked" | "safe_unavailable";

function polishOperatorMessage(message?: string) {
  if (!message) return undefined;
  if (message.includes("script_not_found") || message.includes("run_mutantshield_evolution.py")) {
    return "Evolution Dry-Run is unavailable in this demonstration build. Production models remain protected. Candidate evaluation can be performed through the validated offline/replay workflow.";
  }
  return message;
}

function classifyActionStatus(response: { data: Record<string, unknown> | null; error?: string }): ActionStatus {
  const status = response.data && typeof response.data.status === "string" ? response.data.status : "";
  if (status === "locked_or_unavailable" || status === "safe_unavailable") return "safe_unavailable";
  if (response.error) return "failed";
  return "success";
}

export function DataBadge({ label }: { label: "LIVE" | "REPORT" | "DEMO" | "LOCKED" | "LIVE/REPORT" }) {
  const color =
    label === "LIVE"
      ? "text-[#00ffcc] border-[#00ffcc]/30 bg-[#00ffcc]/10"
      : label === "LOCKED"
        ? "text-[#ff3366] border-[#ff3366]/30 bg-[#ff3366]/10"
        : label === "DEMO"
          ? "text-gray-400 border-white/10 bg-white/5"
          : label === "LIVE/REPORT"
            ? "text-[#fbbf24] border-[#fbbf24]/30 bg-[#fbbf24]/10"
            : "text-[#00d4ff] border-[#00d4ff]/30 bg-[#00d4ff]/10";
  return <Badge variant="outline" className={`${color} border text-[10px] uppercase tracking-wider`}>{label}</Badge>;
}

export function useOperatorActionPanel() {
  const [result, setResult] = useState<{
    name: string;
    status: ActionStatus;
    message?: string;
    data?: unknown;
    timestamp?: string;
  }>({ name: "No action selected", status: "idle" });

  const showLocked = (name: string, message: string, data?: unknown) => {
    setResult({ name, status: "locked", message, data, timestamp: new Date().toLocaleString() });
  };

  const runAction = async (name: string, fn: () => Promise<{ data: Record<string, unknown> | null; error?: string }>) => {
    setResult({ name, status: "running", timestamp: new Date().toLocaleString() });
    const response = await fn();
    setResult({
      name,
      status: classifyActionStatus(response),
      message: polishOperatorMessage(response.error || (response.data?.reason as string | undefined)),
      data: response.data,
      timestamp: new Date().toLocaleString(),
    });
  };

  const color =
    result.status === "success"
      ? "text-[#00ffcc]"
      : result.status === "safe_unavailable"
        ? "text-[#fbbf24]"
      : result.status === "failed" || result.status === "locked"
        ? "text-[#ff3366]"
        : result.status === "running"
          ? "text-[#fbbf24]"
          : "text-gray-400";

  return {
    runAction,
    showLocked,
    Panel: (
      <GlassCard>
        <div className="p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm">Operator Action Result</h3>
            <span className={`text-xs uppercase ${color}`}>{result.status}</span>
          </div>
          <p className="text-xs text-gray-400 mb-2">
            {result.name}{result.timestamp ? ` • ${result.timestamp}` : ""}
          </p>
          {result.message && <p className="text-sm text-[#fbbf24] mb-2">{result.message}</p>}
          <pre className="max-h-56 overflow-auto rounded-lg bg-black/30 border border-white/10 p-3 text-xs text-gray-300">
            {result.data ? JSON.stringify(result.data, null, 2).slice(0, 1400) : result.status === "idle" ? "Awaiting operator action..." : "No action output available for this safe/locked operation."}
          </pre>
        </div>
      </GlassCard>
    ),
  };
}

export function SafeButton({
  children,
  onClick,
  variant = "outline",
  className = "border-white/10",
}: {
  children: ReactNode;
  onClick: () => void;
  variant?: "outline" | "ghost" | "default";
  className?: string;
}) {
  return (
    <Button variant={variant} className={className} onClick={onClick}>
      {children}
    </Button>
  );
}
