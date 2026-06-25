import { AlertTriangle } from "lucide-react";

interface Props {
  offline?: boolean;
  warnings?: string[];
}

export function BackendBanner({ offline, warnings = [] }: Props) {
  if (!offline && warnings.length === 0) return null;
  return (
    <div className="space-y-2">
      {offline && (
        <div className="px-4 py-3 rounded-lg bg-[#ff3366]/10 border border-[#ff3366]/30 flex items-center gap-2">
          <AlertTriangle className="size-4 text-[#ff3366]" />
          <span className="text-sm text-[#ff3366]">Backend Offline — showing last known data where available</span>
        </div>
      )}
      {warnings.map((w) => (
        <div
          key={w}
          className="px-4 py-2 rounded-lg bg-[#fbbf24]/10 border border-[#fbbf24]/30 text-xs text-[#fbbf24]"
        >
          {w}
        </div>
      ))}
    </div>
  );
}

export function StatusBadge({ status }: { status?: string | null }) {
  const s = (status || "UNKNOWN").toUpperCase();
  const color =
    s === "READY" || s === "PASS_DRY_RUN" || s === "BLOCKED_SAFE"
      ? "text-[#00ffcc] border-[#00ffcc]/30 bg-[#00ffcc]/10"
      : s.includes("BLOCK") || s === "FAIL"
        ? "text-[#ff3366] border-[#ff3366]/30 bg-[#ff3366]/10"
        : "text-[#fbbf24] border-[#fbbf24]/30 bg-[#fbbf24]/10";
  return (
    <span className={`inline-flex px-2 py-1 rounded border text-xs font-medium ${color}`}>
      {status || "UNKNOWN"}
    </span>
  );
}
