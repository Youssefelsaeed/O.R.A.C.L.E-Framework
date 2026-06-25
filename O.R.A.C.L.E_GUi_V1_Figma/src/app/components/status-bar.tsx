import { Activity, AlertTriangle, CheckCircle2, Server } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/app/components/ui/tooltip";
import { useEffect, useState } from "react";

export function StatusBar() {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-12 bg-[#0f0f17] border-b border-white/10 flex items-center justify-between px-6">
      {/* Left Section */}
      <div className="flex items-center gap-6">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <div className="size-2 bg-[#00ffcc] rounded-full animate-pulse shadow-[0_0_10px_rgba(0,255,204,0.5)]" />
                <span className="text-xs text-gray-400">System Online</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>All modules operational</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <Server className="size-4 text-[#00d4ff]" />
                <span className="text-xs text-gray-400">8 Nodes</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Distributed processing nodes active</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Center Section - Alert Level */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-gradient-to-r from-yellow-500/10 to-yellow-500/5 border border-yellow-500/20">
              <AlertTriangle className="size-4 text-yellow-400" />
              <span className="text-xs uppercase tracking-wider text-yellow-400">
                Alert Level: Elevated
              </span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>3 active threats detected in the last hour</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Right Section */}
      <div className="flex items-center gap-6">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-[#a855f7]" />
                <span className="text-xs text-gray-400">
                  CPU: 42% | RAM: 68%
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>System resource usage</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-[#00ffcc]" />
                <span className="text-xs text-gray-400 font-mono">
                  {currentTime}
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Last sync: Just now</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
}