import React from "react";
import { CheckCircle2, XCircle, RefreshCw, AlertTriangle, Clock, ArrowRight, ShieldCheck } from "lucide-react";
import { LedgerEntry } from "../types";

interface ReplayTimelineProps {
  entries: LedgerEntry[];
  onSelectEntry: (entry: LedgerEntry) => void;
}

export const ReplayTimeline: React.FC<ReplayTimelineProps> = ({
  entries,
  onSelectEntry
}) => {
  const getIcon = (entry: LedgerEntry) => {
    if (entry.status === "VERIFIED" || entry.status === "VERIFIED_SUCCESS" || entry.status === "PASSED" || entry.status === "APPROVED") {
      return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    }
    if (entry.status === "FAILED") {
      return <XCircle className="w-4 h-4 text-rose-400" />;
    }
    if (entry.status === "RECOVERED" || entry.action.includes("Recovery:")) {
      return <RefreshCw className="w-4 h-4 text-amber-400 animate-spin-slow" />;
    }
    if (entry.status === "CONFLICT_DETECTED" || entry.status === "BLOCKED") {
      return <AlertTriangle className="w-4 h-4 text-rose-400" />;
    }
    return <Clock className="w-4 h-4 text-blue-400" />;
  };

  const getBorderColor = (status: string) => {
    if (status === "VERIFIED" || status === "VERIFIED_SUCCESS" || status === "PASSED" || status === "APPROVED") {
      return "border-emerald-500/40 bg-emerald-950/20";
    }
    if (status === "FAILED") {
      return "border-rose-500/40 bg-rose-950/20";
    }
    if (status === "RECOVERED" || status.includes("RECOVERY")) {
      return "border-amber-500/40 bg-amber-950/20";
    }
    return "border-slate-800 bg-slate-900";
  };

  return (
    <div className="space-y-3">
      {entries.length === 0 ? (
        <div className="text-center py-10 text-slate-500 text-xs font-mono">
          Agent timeline waiting for application initialization...
        </div>
      ) : (
        entries.map((entry, idx) => (
          <div
            key={idx}
            onClick={() => onSelectEntry(entry)}
            className={`p-3.5 rounded-xl border cursor-pointer hover:border-slate-600 transition flex items-start justify-between gap-3 ${getBorderColor(entry.status)}`}
          >
            <div className="flex items-start space-x-3">
              <div className="mt-0.5 shrink-0">{getIcon(entry)}</div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-white">{entry.action}</span>
                  <span className="text-[10px] font-mono text-slate-500">{entry.formatted_time}</span>
                </div>
                {entry.actor && (
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Actor: <span className="font-mono text-indigo-300">{entry.actor}</span>
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${
                entry.status === "VERIFIED" || entry.status === "VERIFIED_SUCCESS"
                  ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                  : entry.status === "FAILED"
                  ? "bg-rose-950 text-rose-300 border-rose-800"
                  : "bg-slate-800 text-slate-300 border-slate-700"
              }`}>
                {entry.status}
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
            </div>
          </div>
        ))
      )}
    </div>
  );
};
