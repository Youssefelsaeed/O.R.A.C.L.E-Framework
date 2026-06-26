import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { ModuleModeCard } from "@/app/components/module-mode-card";
import { DataBadge, useOperatorActionPanel } from "@/app/components/operator-action-panel";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { runGhostTunnelTestTransmit } from "@/app/lib/api";
import { Radio, Signal, Lock, Activity, Globe, Zap } from "lucide-react";

const tunnels = [
  { id: 1, name: "HQ-Field-Alpha", status: "active", latency: 12, encryption: "AES-256", bandwidth: "98%" },
  { id: 2, name: "Cloud-Gateway-01", status: "active", latency: 8, encryption: "Quantum", bandwidth: "87%" },
  { id: 3, name: "Remote-SOC-Beta", status: "standby", latency: 45, encryption: "AES-256", bandwidth: "12%" },
  { id: 4, name: "Partner-Link-07", status: "active", latency: 23, encryption: "Hybrid", bandwidth: "65%" },
];

const communicationLog = [
  { time: "14:24:35", source: "HQ", destination: "Field-Alpha", type: "Command", size: "2.4 KB" },
  { time: "14:23:18", source: "Cloud-Gateway-01", destination: "HQ", type: "Telemetry", size: "156 KB" },
  { time: "14:22:52", source: "HQ", destination: "Remote-SOC-Beta", type: "Alert", size: "8.1 KB" },
  { time: "14:21:09", source: "Partner-Link-07", destination: "HQ", type: "Data Sync", size: "4.2 MB" },
];

export function GhostTunnel() {
  const { data, offline } = useDashboardSummary();
  const action = useOperatorActionPanel();
  const ghost = data?.ghosttunnel;
  const assurance = data?.assurance;

  return (
    <div className="p-8 space-y-6">
      <BackendBanner offline={offline} />
      {action.Panel}
      <ModuleModeCard
        title="GhostTunnel"
        lines={[
          `Fast-Ack: ${ghost?.fast_ack_enabled ? "enabled" : "disabled"}`,
          `Transmit jobs: ${ghost?.jobs_completed ?? 0} completed / ${ghost?.jobs_pending ?? 0} pending / ${ghost?.jobs_failed ?? 0} failed`,
        ]}
      />
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">GhostTunnel</h1>
          <p className="text-sm text-gray-400">
            Fast-ack: {ghost?.fast_ack_enabled ? "enabled" : "disabled"} • Async assurance: {assurance?.async_assurance_enabled ? "ON" : "OFF"}
          </p>
        </div>
        <Button
          className="bg-[#00d4ff] hover:bg-[#00d4ff]/90 text-black"
          onClick={() => action.runAction("Demo Transmit Test", runGhostTunnelTestTransmit)}
        >
          <Zap className="size-4 mr-2" />
          Create New Tunnel
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Jobs Completed <DataBadge label="LIVE/REPORT" /></p>
            <p className="text-2xl font-semibold text-[#00ffcc]">{ghost?.jobs_completed ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Jobs Pending <DataBadge label="LIVE/REPORT" /></p>
            <p className="text-2xl font-semibold text-[#fbbf24]">{ghost?.jobs_pending ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Jobs Failed <DataBadge label="LIVE/REPORT" /></p>
            <p className="text-2xl font-semibold text-[#ff3366]">{ghost?.jobs_failed ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Avg Latency <DataBadge label="REPORT" /></p>
            <p className="text-2xl font-semibold text-[#00d4ff]">
              {ghost?.ghosttunnel_avg_ms != null ? `${ghost.ghosttunnel_avg_ms.toFixed(1)}ms` : "—"}
            </p>
            <StatusBadge status={ghost?.fast_ack_enabled ? "FAST_ACK" : "STANDARD"} />
          </div>
        </GlassCard>
      </div>

      {/* Legacy tunnel view below */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 hidden">
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Active Tunnels
            </p>
            <p className="text-2xl font-semibold text-[#00ffcc]">3</p>
            <p className="text-xs text-gray-500 mt-1">1 on standby</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Avg Latency
            </p>
            <p className="text-2xl font-semibold text-[#00d4ff]">14ms</p>
            <p className="text-xs text-gray-500 mt-1">Excellent</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Data Transferred
            </p>
            <p className="text-2xl font-semibold text-[#a855f7]">127 GB</p>
            <p className="text-xs text-gray-500 mt-1">Last 24h</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Security Level
            </p>
            <p className="text-2xl font-semibold text-[#00ffcc]">Maximum</p>
            <p className="text-xs text-gray-500 mt-1">All encrypted</p>
          </div>
        </GlassCard>
      </div>

      {/* Active Tunnels */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Active Communication Tunnels <DataBadge label="DEMO" /></h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tunnels.map((tunnel) => {
              const statusConfig = {
                active: { color: "text-[#00ffcc]", bg: "bg-[#00ffcc]/10", border: "border-[#00ffcc]/30" },
                standby: { color: "text-[#fbbf24]", bg: "bg-[#fbbf24]/10", border: "border-[#fbbf24]/30" },
              };
              const config = statusConfig[tunnel.status as keyof typeof statusConfig];

              return (
                <div
                  key={tunnel.id}
                  className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#00d4ff]/10 rounded-lg">
                        <Radio className="size-5 text-[#00d4ff]" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm">{tunnel.name}</h4>
                        <Badge className={`${config.bg} ${config.color} ${config.border} border text-xs mt-1`}>
                          {tunnel.status}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Latency</span>
                      <span className="text-xs font-semibold text-[#00ffcc]">{tunnel.latency}ms</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Encryption</span>
                      <span className="text-xs font-semibold">{tunnel.encryption}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Bandwidth Usage</span>
                      <span className="text-xs font-semibold">{tunnel.bandwidth}</span>
                    </div>
                    <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
                      <div
                        className="h-full bg-gradient-to-r from-[#00d4ff] to-[#00ffcc] rounded-full"
                        style={{ width: tunnel.bandwidth }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* Communication Log */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3>Recent Communications <DataBadge label="DEMO" /></h3>
            <div className="flex items-center gap-2">
              <div className="size-2 bg-[#00ffcc] rounded-full animate-pulse" />
              <span className="text-xs text-gray-400">Demo</span>
            </div>
          </div>

          <div className="space-y-2">
            {communicationLog.map((log, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <Signal className="size-4 text-[#00d4ff]" />
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-400">{log.time}</span>
                      <span className="text-gray-500">•</span>
                      <span className="font-semibold">{log.source}</span>
                      <span className="text-gray-500">→</span>
                      <span className="font-semibold">{log.destination}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="border-white/10 text-xs">
                      {log.type}
                    </Badge>
                    <span className="text-xs text-gray-400">{log.size}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Network Topology */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-6">Network Topology <DataBadge label="DEMO" /></h3>
          <div className="flex items-center justify-center min-h-[300px]">
            <div className="relative">
              {/* Central HQ */}
              <div className="size-24 rounded-full bg-gradient-to-br from-[#00d4ff] to-[#a855f7] flex items-center justify-center shadow-[0_0_40px_rgba(0,212,255,0.4)]">
                <div className="text-center">
                  <Globe className="size-6 mx-auto mb-1" />
                  <p className="text-xs font-semibold">HQ</p>
                </div>
              </div>

              {/* Connections */}
              {[
                { angle: 0, distance: 150, label: "Field-Alpha", active: true },
                { angle: 90, distance: 150, label: "Cloud-01", active: true },
                { angle: 180, distance: 150, label: "SOC-Beta", active: false },
                { angle: 270, distance: 150, label: "Partner-07", active: true },
              ].map((node, idx) => {
                const x = Math.cos((node.angle * Math.PI) / 180) * node.distance;
                const y = Math.sin((node.angle * Math.PI) / 180) * node.distance;

                return (
                  <div key={idx}>
                    {/* Connection line */}
                    <div
                      className="absolute top-1/2 left-1/2 h-0.5 origin-left"
                      style={{
                        width: `${node.distance}px`,
                        transform: `rotate(${node.angle}deg)`,
                        background: node.active
                          ? "linear-gradient(to right, #00d4ff, #00ffcc)"
                          : "rgba(255,255,255,0.1)",
                      }}
                    />
                    {/* Node */}
                    <div
                      className={`absolute size-16 rounded-full flex items-center justify-center border-2 ${
                        node.active
                          ? "bg-[#00ffcc]/10 border-[#00ffcc]/30"
                          : "bg-gray-500/10 border-gray-500/30"
                      }`}
                      style={{
                        top: `calc(50% + ${y}px)`,
                        left: `calc(50% + ${x}px)`,
                        transform: "translate(-50%, -50%)",
                      }}
                    >
                      <div className="text-center">
                        <Lock className="size-4 mx-auto mb-1" style={{ color: node.active ? "#00ffcc" : "#666" }} />
                        <p className="text-[10px]">{node.label}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
