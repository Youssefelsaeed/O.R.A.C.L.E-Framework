import { useState } from "react";
import {
  LayoutDashboard,
  Shield,
  Clock,
  Scale,
  Radio,
  Lock,
  Cpu,
  Settings,
} from "lucide-react";
import { GlobalDashboard } from "@/app/components/global-dashboard";
import { MutantShield } from "@/app/components/mutant-shield";
import { ChronoLedger } from "@/app/components/chrono-ledger";
import { EthicQ } from "@/app/components/ethic-q";
import { GhostTunnel } from "@/app/components/ghost-tunnel";
import { QAuthCore } from "@/app/components/qauth-core";
import { AILifecycle } from "@/app/components/ai-lifecycle";
import { SettingsPage } from "@/app/components/settings-page";
import { StatusBar } from "@/app/components/status-bar";

type Page =
  | "dashboard"
  | "mutantshield"
  | "chronoledger"
  | "ethicq"
  | "ghosttunnel"
  | "qauthcore"
  | "ailifecycle"
  | "settings";

const navItems = [
  { id: "dashboard" as Page, icon: LayoutDashboard, label: "Dashboard" },
  { id: "mutantshield" as Page, icon: Shield, label: "MutantShield" },
  { id: "chronoledger" as Page, icon: Clock, label: "ChronoLedger" },
  { id: "ethicq" as Page, icon: Scale, label: "EthicQ" },
  { id: "ghosttunnel" as Page, icon: Radio, label: "GhostTunnel" },
  { id: "qauthcore" as Page, icon: Lock, label: "QAuthCore" },
  { id: "ailifecycle" as Page, icon: Cpu, label: "Evolution Engine" },
  { id: "settings" as Page, icon: Settings, label: "Settings" },
];

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard");

  const renderPage = () => {
    const pageProps = { key: currentPage };
    switch (currentPage) {
      case "dashboard":
        return <GlobalDashboard {...pageProps} />;
      case "mutantshield":
        return <MutantShield {...pageProps} />;
      case "chronoledger":
        return <ChronoLedger {...pageProps} />;
      case "ethicq":
        return <EthicQ {...pageProps} />;
      case "ghosttunnel":
        return <GhostTunnel {...pageProps} />;
      case "qauthcore":
        return <QAuthCore {...pageProps} />;
      case "ailifecycle":
        return <AILifecycle {...pageProps} />;
      case "settings":
        return <SettingsPage {...pageProps} />;
      default:
        return <GlobalDashboard {...pageProps} />;
    }
  };

  return (
    <div className="dark size-full flex flex-col bg-[#0a0a0f] text-foreground overflow-hidden">
      {/* Status Bar */}
      <StatusBar />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation */}
        <nav className="w-64 bg-[#0f0f17] border-r border-white/10 flex flex-col overflow-hidden">
          {/* Logo */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-gradient-to-br from-[#00d4ff] to-[#a855f7] rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(0,212,255,0.3)]">
                <Shield className="size-6 text-white" />
              </div>
              <div>
                <h1 className="text-sm tracking-wider text-[#00d4ff]">
                  PROJECT
                </h1>
                <h2 className="text-base tracking-[0.3em] font-semibold">
                  O.R.A.C.L.E.
                </h2>
              </div>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="flex-1 overflow-y-auto p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? "bg-[#00d4ff]/10 text-[#00d4ff] shadow-[0_0_20px_rgba(0,212,255,0.15)] border border-[#00d4ff]/20"
                      : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
                  }`}
                >
                  <Icon className="size-5" />
                  <span className="text-sm">{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Version Info */}
          <div className="p-4 border-t border-white/10">
            <p className="text-xs text-gray-500">
              Version 2.4.1 • AI Framework
            </p>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-gradient-to-br from-[#0a0a0f] via-[#0a0a0f] to-[#0f0f17]">
          <div className="animate-in fade-in duration-300">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  );
}