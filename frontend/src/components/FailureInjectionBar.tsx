import React from "react";
import { AlertTriangle, Check, X } from "lucide-react";
import { FailureFlags } from "../types";

interface FailureInjectionBarProps {
  flags: FailureFlags;
  onToggleFlag: (key: keyof FailureFlags) => void;
  isOpen: boolean;
}

export const FailureInjectionBar: React.FC<FailureInjectionBarProps> = ({
  flags,
  onToggleFlag,
  isOpen
}) => {
  if (!isOpen) return null;

  return (
    <div className="bg-amber-950/40 border-y border-amber-500/30 px-6 py-3 transition-all animate-fadeIn">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wide">
              Hackathon Failure Injection Deck
            </span>
            <p className="text-[11px] text-amber-200/70">
              Trigger real runtime constraints to test the Evidence Gate & Self-Healing recovery loop.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Flag 1: Oversized Income */}
          <button
            onClick={() => onToggleFlag("reject_oversized_income")}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium border flex items-center space-x-1.5 transition ${
              flags.reject_oversized_income
                ? "bg-amber-500/20 text-amber-200 border-amber-500/60"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span>Oversized Income (5.7MB &gt; 2MB)</span>
            {flags.reject_oversized_income ? <Check className="w-3.5 h-3.5 text-amber-400" /> : <X className="w-3.5 h-3.5 text-slate-500" />}
          </button>

          {/* Flag 2: Strict Photo */}
          <button
            onClick={() => onToggleFlag("strict_photo_requirements")}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium border flex items-center space-x-1.5 transition ${
              flags.strict_photo_requirements
                ? "bg-amber-500/20 text-amber-200 border-amber-500/60"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span>Strict Photo (JPG 200x230)</span>
            {flags.strict_photo_requirements ? <Check className="w-3.5 h-3.5 text-amber-400" /> : <X className="w-3.5 h-3.5 text-slate-500" />}
          </button>

          {/* Flag 3: Session Expire */}
          <button
            onClick={() => onToggleFlag("simulate_session_expire")}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium border flex items-center space-x-1.5 transition ${
              flags.simulate_session_expire
                ? "bg-rose-500/20 text-rose-200 border-rose-500/60"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span>Session Expire (401)</span>
            {flags.simulate_session_expire ? <Check className="w-3.5 h-3.5 text-rose-400" /> : <X className="w-3.5 h-3.5 text-slate-500" />}
          </button>

          {/* Flag 4: Save Timeout */}
          <button
            onClick={() => onToggleFlag("simulate_save_timeout")}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium border flex items-center space-x-1.5 transition ${
              flags.simulate_save_timeout
                ? "bg-purple-500/20 text-purple-200 border-purple-500/60"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span>Save Timeout (UNKNOWN)</span>
            {flags.simulate_save_timeout ? <Check className="w-3.5 h-3.5 text-purple-400" /> : <X className="w-3.5 h-3.5 text-slate-500" />}
          </button>

          {/* Flag 5: Schema Change */}
          <button
            onClick={() => onToggleFlag("simulate_schema_change")}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium border flex items-center space-x-1.5 transition ${
              flags.simulate_schema_change
                ? "bg-blue-500/20 text-blue-200 border-blue-500/60"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span>Schema Change</span>
            {flags.simulate_schema_change ? <Check className="w-3.5 h-3.5 text-blue-400" /> : <X className="w-3.5 h-3.5 text-slate-500" />}
          </button>
        </div>
      </div>
    </div>
  );
};
