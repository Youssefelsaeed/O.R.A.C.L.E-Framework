import { cn } from "@/app/components/ui/utils";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  glowColor?: "blue" | "teal" | "violet" | "red";
}

export function GlassCard({
  children,
  className,
  glow = false,
  glowColor = "blue",
}: GlassCardProps) {
  const glowColors = {
    blue: "shadow-[0_0_30px_rgba(0,212,255,0.15)]",
    teal: "shadow-[0_0_30px_rgba(0,255,204,0.15)]",
    violet: "shadow-[0_0_30px_rgba(168,85,247,0.15)]",
    red: "shadow-[0_0_30px_rgba(255,51,102,0.15)]",
  };

  return (
    <div
      className={cn(
        "rounded-xl bg-gradient-to-br from-white/[0.05] to-white/[0.02] backdrop-blur-sm border border-white/10 transition-all duration-200",
        glow && glowColors[glowColor],
        className
      )}
    >
      {children}
    </div>
  );
}