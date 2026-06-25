import { FileText, ExternalLink } from "lucide-react";
import { API_BASE } from "@/app/lib/api";

const REPORTS = [
  { id: "backend_validation", label: "Backend Validation Report" },
  { id: "evolution_run", label: "Evolution Run Report" },
  { id: "evaluation_gate", label: "Evaluation Gate Report" },
  { id: "production_baseline", label: "Production Baseline Metrics" },
  { id: "chronoledger_evidence", label: "ChronoLedger Evidence Report" },
] as const;

export function ReportLinks() {
  return (
    <div className="space-y-2">
      {REPORTS.map((r) => (
        <a
          key={r.id}
          href={`${API_BASE}/oracle/dashboard/reports/${r.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all text-sm group"
        >
          <span className="flex items-center gap-2 text-gray-300 group-hover:text-white">
            <FileText className="size-4 text-[#00d4ff]" />
            {r.label}
          </span>
          <ExternalLink className="size-4 text-gray-500 group-hover:text-[#00d4ff]" />
        </a>
      ))}
    </div>
  );
}
