import { AlertTriangle } from "lucide-react";

interface Props {
  warnings?: string[];
  title?: string;
}

export function SystemWarnings({ warnings = [], title = "System Warnings" }: Props) {
  if (!warnings.length) {
    return (
      <div className="p-4 rounded-lg bg-white/5 border border-white/10 text-sm text-gray-500">
        No active system warnings
      </div>
    );
  }
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <AlertTriangle className="size-4 text-[#fbbf24]" />
        {title}
      </h3>
      {warnings.map((w) => (
        <div
          key={w}
          className="px-4 py-3 rounded-lg bg-[#fbbf24]/10 border border-[#fbbf24]/30 text-sm text-[#fbbf24]"
        >
          {w}
        </div>
      ))}
    </div>
  );
}
