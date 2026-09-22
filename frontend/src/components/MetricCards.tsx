import React from "react";
import { CheckCircle2, AlertOctagon, RefreshCw, FileText, ShieldAlert } from "lucide-react";
import { ApplicationMetrics } from "../types";

interface MetricCardsProps {
  metrics: ApplicationMetrics | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics }) => {
  const m = metrics || {
    total_actions: 0,
    verified_actions: 0,
    failed_actions: 0,
    recovery_count: 0,
    fields_verified: "0 / 14",
    documents_verified: "0 / 4",
    unresolved_conflicts: 0,
    submission_status: "NOT_STARTED"
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5 my-5">
      {/* Card 1: Verified Actions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>Verified Actions</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-2xl font-mono font-extrabold text-white">
          {m.verified_actions} <span className="text-xs text-slate-500 font-normal">/ {m.total_actions}</span>
        </div>
        <div className="text-[11px] text-emerald-400/90 mt-1 flex items-center space-x-1">
          <span>Deterministic proof stored</span>
        </div>
      </div>

      {/* Card 2: Self-Healing Recoveries */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>Self-Healing Recoveries</span>
          <RefreshCw className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-mono font-extrabold text-white">
          {m.recovery_count}
        </div>
        <div className="text-[11px] text-amber-400/90 mt-1 flex items-center space-x-1">
          <span>Bounded adaptations passed</span>
        </div>
      </div>

      {/* Card 3: Fields Verified */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>Fields Verified</span>
          <FileText className="w-4 h-4 text-blue-400" />
        </div>
        <div className="text-2xl font-mono font-extrabold text-white">
          {m.fields_verified}
        </div>
        <div className="text-[11px] text-blue-400/90 mt-1 flex items-center space-x-1">
          <span>Zero fabrication policy</span>
        </div>
      </div>

      {/* Card 4: Documents Verified */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>Documents Verified</span>
          <CheckCircle2 className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="text-2xl font-mono font-extrabold text-white">
          {m.documents_verified}
        </div>
        <div className="text-[11px] text-indigo-400/90 mt-1 flex items-center space-x-1">
          <span>Checksums confirmed</span>
        </div>
      </div>

      {/* Card 5: Gate Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden col-span-2 md:col-span-1">
        <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>Evidence Gate</span>
          <ShieldAlert className="w-4 h-4 text-rose-400" />
        </div>
        <div className="text-sm font-mono font-extrabold text-slate-100 flex items-center space-x-1.5 mt-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>ARMED & PROVING</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Zero-Trust State Barrier
        </div>
      </div>
    </div>
  );
};
