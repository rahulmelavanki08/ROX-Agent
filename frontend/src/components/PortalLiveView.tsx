import React from "react";
import { Globe, RefreshCw, ExternalLink } from "lucide-react";

interface PortalLiveViewProps {
  portalSessionId: string | null;
  refreshTrigger: number;
}

export const PortalLiveView: React.FC<PortalLiveViewProps> = ({
  portalSessionId,
  refreshTrigger
}) => {
  if (!portalSessionId) {
    return (
      <div className="h-full min-h-[350px] bg-slate-900 border border-slate-800 rounded-2xl flex flex-col items-center justify-center p-6 text-center text-slate-500">
        <Globe className="w-8 h-8 mb-2 opacity-40" />
        <p className="text-xs font-mono">No active portal session connected.</p>
      </div>
    );
  }

  const portalUrl = `http://127.0.0.1:8000/portal/view/${portalSessionId}?t=${refreshTrigger}`;

  return (
    <div className="h-full min-h-[420px] bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-lg">
      <div className="px-4 py-2.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-mono text-white font-semibold">Simulated Scholarship Portal Web DOM</span>
        </div>
        <div className="flex items-center space-x-3">
          <a
            href={portalUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 font-mono text-[11px]"
          >
            <span>Open Tab</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
      <iframe
        src={portalUrl}
        className="w-full flex-1 border-0 bg-white"
        title="Simulated Portal Live View"
      />
    </div>
  );
};
