import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner, StatusBadge } from "@/app/components/backend-banner";
import { ModuleModeCard } from "@/app/components/module-mode-card";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { Lock, Key, Shield, Users, Activity, CheckCircle2, AlertTriangle } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const authMethods = [
  {
    name: "Quantum Key Distribution",
    icon: Key,
    status: "active",
    strength: 100,
    usage: 234,
    color: "#00d4ff",
  },
  {
    name: "Biometric Multi-Factor",
    icon: Shield,
    status: "active",
    strength: 98,
    usage: 567,
    color: "#00ffcc",
  },
  {
    name: "Hardware Tokens",
    icon: Lock,
    status: "active",
    strength: 95,
    usage: 189,
    color: "#a855f7",
  },
];

const sessionData = [
  { name: "Active", value: 42, color: "#00ffcc" },
  { name: "Idle", value: 15, color: "#fbbf24" },
  { name: "Expired", value: 8, color: "#9ca3af" },
];

const recentAuth = [
  { time: "14:24:35", user: "admin@oracle.sec", method: "Quantum Key", status: "success", location: "HQ - Operations" },
  { time: "14:23:18", user: "analyst-2@oracle.sec", method: "Biometric", status: "success", location: "SOC - Terminal 7" },
  { time: "14:22:52", user: "unknown@external.net", method: "Password", status: "failed", location: "External - 203.0.113.42" },
  { time: "14:21:09", user: "service-bot-01", method: "Hardware Token", status: "success", location: "Cloud Gateway" },
  { time: "14:19:47", user: "contractor@partner.com", method: "Biometric", status: "failed", location: "Remote - VPN" },
];

export function QAuthCore() {
  const { data, offline } = useDashboardSummary();
  const assurance = data?.assurance;
  const moduleOk = data?.modules?.qauthcore;

  return (
    <div className="p-8 space-y-6">
      <BackendBanner offline={offline} />
      <ModuleModeCard
        title="QAuthCore"
        lines={["Entropy: local hot path + deferred quantum assurance"]}
      />
      <GlassCard>
        <div className="p-5 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div><p className="text-gray-400 text-xs">Module Health</p><StatusBadge status={moduleOk ? "ACTIVE" : "OFFLINE"} /></div>
          <div><p className="text-gray-400 text-xs">Async Assurance</p><p>{assurance?.async_assurance_enabled ? "enabled" : "disabled"}</p></div>
          <div><p className="text-gray-400 text-xs">Assurance Completed</p><p className="font-semibold">{assurance?.latest_completed ?? "—"}</p></div>
        </div>
      </GlassCard>
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">QAuthCore</h1>
          <p className="text-sm text-gray-400">
            Quantum-resistant authentication and access control
          </p>
        </div>
        <Button className="bg-[#00d4ff] hover:bg-[#00d4ff]/90 text-black">
          <Users className="size-4 mr-2" />
          Manage Users
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard glow glowColor="teal">
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Active Sessions
            </p>
            <p className="text-2xl font-semibold text-[#00ffcc]">42</p>
            <p className="text-xs text-gray-500 mt-1">Across all systems</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Auth Success Rate
            </p>
            <p className="text-2xl font-semibold text-[#00d4ff]">98.7%</p>
            <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Failed Attempts
            </p>
            <p className="text-2xl font-semibold text-[#ff3366]">23</p>
            <p className="text-xs text-gray-500 mt-1">Suspicious: 5</p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Registered Users
            </p>
            <p className="text-2xl font-semibold text-[#a855f7]">187</p>
            <p className="text-xs text-gray-500 mt-1">+3 this week</p>
          </div>
        </GlassCard>
      </div>

      {/* Authentication Methods */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Authentication Methods</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {authMethods.map((method) => {
              const Icon = method.icon;
              return (
                <div
                  key={method.name}
                  className="p-5 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div
                      className="p-3 rounded-lg"
                      style={{ backgroundColor: `${method.color}15` }}
                    >
                      <Icon className="size-6" style={{ color: method.color }} />
                    </div>
                    <Badge className="bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30 border text-xs">
                      {method.status}
                    </Badge>
                  </div>

                  <h4 className="font-semibold mb-1 text-sm">{method.name}</h4>
                  <p className="text-xs text-gray-400 mb-4">
                    {method.usage} authentications today
                  </p>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">Security Strength</span>
                      <span className="text-xs font-semibold" style={{ color: method.color }}>
                        {method.strength}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${method.strength}%`,
                          backgroundColor: method.color,
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* Session Analytics & Recent Auth */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session Distribution */}
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Session Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sessionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {sessionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#12121a",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-4">
              {sessionData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="size-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-xs text-gray-400">{item.name}</span>
                  </div>
                  <span className="text-xs font-semibold">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>

        {/* Recent Authentication Log */}
        <GlassCard className="lg:col-span-2">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3>Recent Authentication Events</h3>
              <div className="flex items-center gap-2">
                <div className="size-2 bg-[#00ffcc] rounded-full animate-pulse" />
                <span className="text-xs text-gray-400">Live</span>
              </div>
            </div>

            <div className="space-y-2">
              {recentAuth.map((auth, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        {auth.status === "success" ? (
                          <Badge className="bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30 border text-xs">
                            <CheckCircle2 className="size-3 mr-1" />
                            Success
                          </Badge>
                        ) : (
                          <Badge className="bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30 border text-xs">
                            <AlertTriangle className="size-3 mr-1" />
                            Failed
                          </Badge>
                        )}
                        <span className="text-xs text-gray-500">{auth.time}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 mt-2">
                        <div>
                          <p className="text-xs text-gray-400">User</p>
                          <p className="text-xs font-semibold truncate">{auth.user}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400">Method</p>
                          <p className="text-xs font-semibold">{auth.method}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400">Location</p>
                          <p className="text-xs font-semibold truncate">{auth.location}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Security Alerts */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Security Alerts</h3>
          <div className="space-y-3">
            <div className="p-4 rounded-lg bg-[#fbbf24]/5 border border-[#fbbf24]/20">
              <div className="flex items-start gap-3">
                <AlertTriangle className="size-5 text-[#fbbf24] mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[#fbbf24] mb-1">
                    Multiple Failed Login Attempts Detected
                  </p>
                  <p className="text-xs text-gray-400 mb-2">
                    IP: 203.0.113.42 attempted 5 failed logins in the last 10 minutes
                  </p>
                  <Button size="sm" variant="outline" className="border-[#fbbf24]/30 text-[#fbbf24] hover:bg-[#fbbf24]/10">
                    Block IP Address
                  </Button>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-[#00ffcc]/5 border border-[#00ffcc]/20">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="size-5 text-[#00ffcc] mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[#00ffcc] mb-1">
                    All Systems Secured
                  </p>
                  <p className="text-xs text-gray-400">
                    No suspicious authentication patterns detected in the last 6 hours
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
