import { GlassCard } from "@/app/components/glass-card";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Switch } from "@/app/components/ui/switch";
import { Badge } from "@/app/components/ui/badge";
import {
  Key,
  Zap,
  Bell,
  Users,
  Shield,
  Globe,
  Database,
  Eye,
  EyeOff,
  Copy,
  RefreshCw,
} from "lucide-react";
import { useState } from "react";
import { SAFETY_BLOCKED_MSG } from "@/app/lib/api";
import { Lock } from "lucide-react";

const apiKeys = [
  {
    name: "Production API Key",
    key: "ora_prod_xk8j2m9f3h7s4p1q6w0e",
    created: "2025-11-15",
    lastUsed: "2 hours ago",
    status: "active",
  },
  {
    name: "Development API Key",
    key: "ora_dev_r5t8y2u9i4o3p1a7s6d",
    created: "2026-01-05",
    lastUsed: "5 min ago",
    status: "active",
  },
  {
    name: "Backup API Key",
    key: "ora_backup_f3g7h2j5k8l1m4n9p0q",
    created: "2025-12-01",
    lastUsed: "Never",
    status: "inactive",
  },
];

const siemIntegrations = [
  { name: "Splunk Enterprise", icon: Database, enabled: true, status: "connected" },
  { name: "Elastic Stack (ELK)", icon: Zap, enabled: true, status: "connected" },
  { name: "IBM QRadar", icon: Shield, enabled: false, status: "not configured" },
  { name: "Microsoft Sentinel", icon: Globe, enabled: false, status: "not configured" },
];

const userRoles = [
  { name: "Security Analyst", users: 12, permissions: ["View", "Analyze", "Respond"] },
  { name: "SOC Manager", users: 3, permissions: ["View", "Analyze", "Respond", "Configure"] },
  { name: "Admin", users: 2, permissions: ["Full Access"] },
  { name: "Auditor", users: 4, permissions: ["View", "Export"] },
];

export function SettingsPage() {
  const [showKeys, setShowKeys] = useState<{ [key: string]: boolean }>({});

  const toggleKeyVisibility = (keyName: string) => {
    setShowKeys((prev) => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  const maskKey = (key: string, visible: boolean) => {
    if (visible) return key;
    return key.slice(0, 12) + "•".repeat(key.length - 16) + key.slice(-4);
  };

  return (
    <div className="p-8 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl mb-1">Settings & Integrations</h1>
        <p className="text-sm text-gray-400">
          System configuration, API management, and third-party integrations
        </p>
      </div>

      <GlassCard glow glowColor="violet">
        <div className="p-6">
          <h3 className="mb-1 flex items-center gap-2">
            <Lock className="size-5 text-[#fbbf24]" />
            ORACLE Safety Controls
          </h3>
          <p className="text-sm text-gray-400 mb-4">
            Destructive and promotion actions are disabled by policy.
          </p>
          <div className="space-y-3">
            {[
              "Real model promotion",
              "Force promote",
              "Auto promote",
              "Delete logs",
              "Delete models",
            ].map((control) => (
              <div
                key={control}
                className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-[#ff3366]/20 opacity-60"
              >
                <span className="text-sm">{control}</span>
                <span className="text-xs text-[#ff3366]">{SAFETY_BLOCKED_MSG}</span>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* API Key Management */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="mb-1">API Key Management</h3>
              <p className="text-sm text-gray-400">
                Manage API keys for programmatic access to O.R.A.C.L.E.
              </p>
            </div>
            <Button className="bg-[#00d4ff] hover:bg-[#00d4ff]/90 text-black">
              <Key className="size-4 mr-2" />
              Generate New Key
            </Button>
          </div>

          <div className="space-y-3">
            {apiKeys.map((apiKey) => (
              <div
                key={apiKey.name}
                className="p-4 rounded-lg bg-white/5 border border-white/10"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-sm">{apiKey.name}</h4>
                      <Badge
                        className={
                          apiKey.status === "active"
                            ? "bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30 border"
                            : "bg-gray-500/10 text-gray-400 border-gray-500/30 border"
                        }
                      >
                        {apiKey.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <code className="text-xs font-mono px-3 py-1.5 bg-black/30 rounded border border-white/10">
                        {maskKey(apiKey.key, showKeys[apiKey.name] || false)}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleKeyVisibility(apiKey.name)}
                        className="text-gray-400 hover:text-white"
                      >
                        {showKeys[apiKey.name] ? (
                          <EyeOff className="size-4" />
                        ) : (
                          <Eye className="size-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-white"
                      >
                        <Copy className="size-4" />
                      </Button>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span>Created: {apiKey.created}</span>
                      <span>•</span>
                      <span>Last used: {apiKey.lastUsed}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-[#00d4ff] hover:text-[#00d4ff]/80"
                    >
                      <RefreshCw className="size-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-[#ff3366] hover:text-[#ff3366]/80"
                    >
                      Revoke
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* SIEM Integrations */}
      <GlassCard>
        <div className="p-6">
          <div className="mb-4">
            <h3 className="mb-1">SIEM Integrations</h3>
            <p className="text-sm text-gray-400">
              Connect O.R.A.C.L.E. with your existing security information and event
              management systems
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {siemIntegrations.map((integration) => {
              const Icon = integration.icon;
              return (
                <div
                  key={integration.name}
                  className="p-5 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#00d4ff]/10 rounded-lg">
                        <Icon className="size-5 text-[#00d4ff]" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm">{integration.name}</h4>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {integration.status}
                        </p>
                      </div>
                    </div>
                    <Switch checked={integration.enabled} />
                  </div>
                  {integration.enabled ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full border-white/10"
                    >
                      Configure
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full border-[#00d4ff]/30 text-[#00d4ff]"
                    >
                      Set Up Integration
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* Alert Routing Rules */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="mb-1">Alert Routing Rules</h3>
              <p className="text-sm text-gray-400">
                Configure how alerts are distributed to different teams
              </p>
            </div>
            <Button variant="outline" className="border-white/10">
              <Bell className="size-4 mr-2" />
              Add Rule
            </Button>
          </div>

          <div className="space-y-3">
            {[
              {
                severity: "Critical",
                destination: "SOC Manager + On-Call",
                method: "Email, SMS, Slack",
                color: "#ff3366",
              },
              {
                severity: "High",
                destination: "SOC Team",
                method: "Email, Slack",
                color: "#ff9500",
              },
              {
                severity: "Medium",
                destination: "Security Analysts",
                method: "Dashboard, Email",
                color: "#fbbf24",
              },
              {
                severity: "Low",
                destination: "Dashboard Only",
                method: "Dashboard",
                color: "#00ffcc",
              },
            ].map((rule) => (
              <div
                key={rule.severity}
                className="p-4 rounded-lg bg-white/5 border border-white/10 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <Badge
                    variant="outline"
                    className="border-white/10"
                    style={{ color: rule.color }}
                  >
                    {rule.severity}
                  </Badge>
                  <div>
                    <p className="text-sm font-semibold">{rule.destination}</p>
                    <p className="text-xs text-gray-400">{rule.method}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="text-gray-400">
                  Edit
                </Button>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* User Roles & Permissions */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="mb-1">User Roles & Permissions</h3>
              <p className="text-sm text-gray-400">
                Manage access control and user permissions
              </p>
            </div>
            <Button variant="outline" className="border-white/10">
              <Users className="size-4 mr-2" />
              Manage Users
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {userRoles.map((role) => (
              <div
                key={role.name}
                className="p-4 rounded-lg bg-white/5 border border-white/10"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-sm mb-1">{role.name}</h4>
                    <p className="text-xs text-gray-400">{role.users} users</p>
                  </div>
                  <Badge variant="outline" className="border-white/10">
                    {role.permissions.length} perms
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {role.permissions.map((perm) => (
                    <Badge
                      key={perm}
                      className="bg-[#00d4ff]/10 text-[#00d4ff] border-[#00d4ff]/30 border text-xs"
                    >
                      {perm}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* System Preferences */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">System Preferences</h3>
          <div className="space-y-4">
            {[
              {
                label: "Enable Real-time Monitoring",
                description: "Continuously monitor for threats",
                enabled: true,
              },
              {
                label: "Auto-block Suspicious IPs",
                description: "Automatically block IPs with high threat scores",
                enabled: true,
              },
              {
                label: "Require Human Approval for Critical Actions",
                description: "Human authorization needed for high-risk responses",
                enabled: true,
              },
              {
                label: "Send Daily Security Reports",
                description: "Email summary reports every morning",
                enabled: false,
              },
              {
                label: "Enable Audit Logging",
                description: "Log all system actions to ChronoLedger",
                enabled: true,
              },
            ].map((pref) => (
              <div
                key={pref.label}
                className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10"
              >
                <div>
                  <p className="text-sm font-semibold mb-1">{pref.label}</p>
                  <p className="text-xs text-gray-400">{pref.description}</p>
                </div>
                <Switch checked={pref.enabled} />
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
