import { GlassCard } from "@/app/components/glass-card";
import { BackendBanner } from "@/app/components/backend-banner";
import { ModuleModeCard } from "@/app/components/module-mode-card";
import { Button } from "@/app/components/ui/button";
import { useDashboardSummary } from "@/app/lib/use-oracle-data";
import { fetchLatestEvents, SAFETY_BLOCKED_MSG } from "@/app/lib/api";
import { useEffect, useState } from "react";
import { Input } from "@/app/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/app/components/ui/table";
import { Badge } from "@/app/components/ui/badge";
import {
  Search,
  Download,
  CheckCircle2,
  AlertTriangle,
  Link2,
  Filter,
} from "lucide-react";

const blockchainBlocks = [
  {
    blockId: 12847,
    hash: "0x7f9a3b2c...8d4e1a5f",
    timestamp: "2026-01-13 14:24:35",
    events: 23,
    status: "verified",
    eventSummary: "Auth attempts, API calls, data access",
  },
  {
    blockId: 12846,
    hash: "0x3c8d1f4a...2b9e7c6d",
    timestamp: "2026-01-13 14:19:12",
    events: 45,
    status: "verified",
    eventSummary: "Network traffic logs, firewall events",
  },
  {
    blockId: 12845,
    hash: "0x9e2f5b1c...4a8d3f7e",
    timestamp: "2026-01-13 14:14:58",
    events: 31,
    status: "verified",
    eventSummary: "User sessions, privilege escalations",
  },
  {
    blockId: 12844,
    hash: "0x5b7c2e9a...1f4d8b3c",
    timestamp: "2026-01-13 14:09:43",
    events: 67,
    status: "verified",
    eventSummary: "Database queries, admin actions",
  },
  {
    blockId: 12843,
    hash: "0x1a4f8c2e...7b9d5e3a",
    timestamp: "2026-01-13 14:04:27",
    events: 19,
    status: "pending",
    eventSummary: "Config changes, system updates",
  },
  {
    blockId: 12842,
    hash: "0x8d3e1b7f...5c2a9f4e",
    timestamp: "2026-01-13 13:59:15",
    events: 52,
    status: "verified",
    eventSummary: "Email gateway, file transfers",
  },
];

const recentEvents = [
  { time: "14:24:35", type: "Authentication", user: "admin@oracle.sec", action: "Login successful" },
  { time: "14:24:18", type: "API Access", user: "service-bot-01", action: "GET /api/threats" },
  { time: "14:24:01", type: "Firewall", user: "system", action: "Blocked: 203.0.113.42" },
  { time: "14:23:42", type: "Database", user: "api-worker-3", action: "Query: SELECT users" },
];

export function ChronoLedger() {
  const { data, offline } = useDashboardSummary();
  const chrono = data?.chronoledger_evidence;
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    fetchLatestEvents().then((r) => setEvents(r.data?.events || []));
  }, []);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl mb-1">ChronoLedger</h1>
          <p className="text-sm text-gray-400">
            Immutable audit trail — integrity-trusted, label-trust requires human review
          </p>
        </div>
        <Button variant="outline" className="border-white/10 opacity-50" onClick={() => alert(SAFETY_BLOCKED_MSG)} disabled>
          <Download className="size-4 mr-2" />
          Export (restricted)
        </Button>
      </div>

      <BackendBanner offline={offline} />
      <ModuleModeCard
        title="ChronoLedger"
        lines={[
          "Storage: SQLite dev mode / PostgreSQL production-ready",
          "Assurance: provisional → quantum_verified",
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase mb-2">Evidence Count</p>
            <p className="text-2xl font-semibold text-[#00d4ff]">{chrono?.total_events ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase mb-2">False Positive Candidates</p>
            <p className="text-2xl font-semibold text-[#fbbf24]">{chrono?.false_positive_candidate ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase mb-2">Outlier Candidates</p>
            <p className="text-2xl font-semibold text-[#a855f7]">{chrono?.outlier_candidate ?? "—"}</p>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="p-5">
            <p className="text-xs text-gray-400 uppercase mb-2">Unverified</p>
            <p className="text-2xl font-semibold text-[#ff3366]">{chrono?.unverified_count ?? "—"}</p>
          </div>
        </GlassCard>
      </div>

      {events.length > 0 && (
        <GlassCard>
          <div className="p-6">
            <h3 className="mb-4">Latest Evidence Events (from reports)</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {events.slice(0, 10).map((e, i) => (
                <div key={i} className="p-3 rounded-lg bg-white/5 border border-white/10 text-xs">
                  <p className="font-semibold">{String(e.flow_id)} • {String(e.risk_label)}</p>
                  <p className="text-gray-400">Bucket: {String(e.evidence_bucket)} • Trust: {String(e.label_trust)}</p>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      )}

      {/* Blockchain Explorer */}
      {/* Search and Filter */}
      <GlassCard>
        <div className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
              <Input
                placeholder="Search by block ID, hash, or event type..."
                className="pl-10 bg-white/5 border-white/10"
              />
            </div>
            <Button variant="outline" className="border-white/10">
              <Filter className="size-4 mr-2" />
              Filters
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* Blockchain Explorer Table */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-4">Blockchain Log Blocks</h3>
          <div className="border border-white/10 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-white/5">
                  <TableHead className="text-gray-400">Block ID</TableHead>
                  <TableHead className="text-gray-400">Hash</TableHead>
                  <TableHead className="text-gray-400">Timestamp</TableHead>
                  <TableHead className="text-gray-400">Events</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Summary</TableHead>
                  <TableHead className="text-gray-400"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {blockchainBlocks.map((block) => (
                  <TableRow
                    key={block.blockId}
                    className="border-white/10 hover:bg-white/5"
                  >
                    <TableCell className="font-mono text-[#00d4ff]">
                      #{block.blockId}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-gray-400">
                      {block.hash}
                    </TableCell>
                    <TableCell className="text-sm">{block.timestamp}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-white/10">
                        {block.events}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {block.status === "verified" ? (
                        <Badge className="bg-[#00ffcc]/10 text-[#00ffcc] border-[#00ffcc]/30 border">
                          <CheckCircle2 className="size-3 mr-1" />
                          Verified
                        </Badge>
                      ) : (
                        <Badge className="bg-[#fbbf24]/10 text-[#fbbf24] border-[#fbbf24]/30 border">
                          <AlertTriangle className="size-3 mr-1" />
                          Pending
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-gray-400 max-w-xs truncate">
                      {block.eventSummary}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-[#00d4ff] hover:text-[#00d4ff]/80"
                      >
                        <Link2 className="size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </GlassCard>

      {/* Recent Events Stream */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3>Recent Event Stream</h3>
            <div className="flex items-center gap-2">
              <div className="size-2 bg-[#00ffcc] rounded-full animate-pulse" />
              <span className="text-xs text-gray-400">Live</span>
            </div>
          </div>

          <div className="space-y-2">
            {recentEvents.map((event, idx) => (
              <div
                key={idx}
                className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-[#00d4ff]/30 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <Badge
                        variant="outline"
                        className="border-white/10 text-xs"
                      >
                        {event.type}
                      </Badge>
                      <span className="text-xs text-gray-400">{event.time}</span>
                    </div>
                    <p className="text-sm mb-1">{event.action}</p>
                    <p className="text-xs text-gray-500">User: {event.user}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Chain Visualization */}
      <GlassCard>
        <div className="p-6">
          <h3 className="mb-6">Block Chain Visualization</h3>
          <div className="flex items-center justify-center gap-4 overflow-x-auto pb-4">
            {blockchainBlocks.slice(0, 5).reverse().map((block, idx) => (
              <div key={block.blockId} className="flex items-center">
                <div className="flex flex-col items-center min-w-[120px]">
                  <div className="size-16 rounded-lg bg-gradient-to-br from-[#00d4ff]/20 to-[#a855f7]/20 border border-[#00d4ff]/30 flex items-center justify-center shadow-[0_0_20px_rgba(0,212,255,0.2)]">
                    <div className="text-center">
                      <p className="text-xs text-gray-400">Block</p>
                      <p className="text-sm font-semibold text-[#00d4ff]">
                        {block.blockId}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2 text-center">
                    {block.events} events
                  </p>
                  {block.status === "verified" && (
                    <CheckCircle2 className="size-4 text-[#00ffcc] mt-1" />
                  )}
                </div>
                {idx < 4 && (
                  <div className="flex items-center gap-1 mx-2">
                    <div className="w-8 h-0.5 bg-[#00d4ff]" />
                    <div className="size-1 bg-[#00d4ff] rounded-full" />
                    <div className="w-8 h-0.5 bg-[#00d4ff]" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
