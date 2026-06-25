import { GlassCard } from "@/app/components/glass-card";

interface Props {
  title: string;
  lines: string[];
}

export function ModuleModeCard({ title, lines }: Props) {
  return (
    <GlassCard>
      <div className="p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">{title} — Architecture Mode</p>
        <ul className="space-y-1">
          {lines.map((line) => (
            <li key={line} className="text-sm text-gray-300">
              • {line}
            </li>
          ))}
        </ul>
      </div>
    </GlassCard>
  );
}
