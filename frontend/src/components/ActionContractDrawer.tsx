import React from "react";
import { X, ShieldCheck, AlertOctagon, Terminal, FileCode, CheckCircle2 } from "lucide-react";
import { ActionContract } from "../types";

interface ActionContractDrawerProps {
  contract: ActionContract | null;
  onClose: () => void;
  isOpen: boolean;
}

export const ActionContractDrawer: React.FC<ActionContractDrawerProps> = ({
  contract,
  onClose,
  isOpen
}) => {
  if (!isOpen || !contract) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "VERIFIED":
        return "text-emerald-400 bg-emerald-950/80 border-emerald-800";
      case "FAILED":
        return "text-rose-400 bg-rose-950/80 border-rose-800";
      case "RECOVERING":
        return "text-amber-400 bg-amber-950/80 border-amber-800";
      default:
        return "text-blue-400 bg-blue-950/80 border-blue-800";
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-slideLeft">
      {/* Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-blue-400 font-bold">{contract.action_id}</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${getStatusColor(contract.status)}`}>
              {contract.status}
            </span>
          </div>
          <h3 className="text-base font-bold text-white mt-1">{contract.name}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Contract Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* 1. Action Metadata */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">1. ACTION SPECIFICATION</span>
          <div className="text-xs font-mono text-slate-300">
            <div>Category: <span className="text-white">{contract.step_category}</span></div>
            <div>Risk Level: <span className="text-amber-400">{contract.risk_level}</span></div>
            <div>Attempt: <span className="text-blue-400">{contract.attempt} / {contract.max_attempts}</span></div>
          </div>
        </div>

        {/* 2. Preconditions */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">2. PRECONDITIONS</span>
          <ul className="space-y-1 text-xs font-mono">
            {contract.preconditions.map((pre, i) => (
              <li key={i} className="flex items-center space-x-2 text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{pre}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 3. Execution Command */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">3. EXECUTION DISPATCH</span>
          <code className="text-xs font-mono text-blue-300 bg-slate-900 px-2 py-1 rounded block overflow-x-auto border border-slate-800">
            {contract.execution_command}
          </code>
        </div>

        {/* 4. Observation */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">4. RAW OBSERVATION</span>
          <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 p-2.5 rounded border border-slate-800 overflow-x-auto max-h-40">
            {JSON.stringify(contract.observation || {}, null, 2)}
          </pre>
        </div>

        {/* 5. Postconditions */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">5. POSTCONDITIONS</span>
          <ul className="space-y-1 text-xs font-mono">
            {contract.postconditions.map((post, i) => {
              const passed = contract.postcondition_results ? contract.postcondition_results[post] !== false : true;
              return (
                <li key={i} className={`flex items-center space-x-2 ${passed ? "text-emerald-400" : "text-rose-400"}`}>
                  <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                  <span>{post}: {passed ? "PASSED" : "FAILED"}</span>
                </li>
              );
            })}
          </ul>
        </div>

        {/* 6. Machine Evidence */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 block mb-1">6. DETERMINISTIC EVIDENCE ARTIFACT</span>
          <pre className="text-[11px] font-mono text-emerald-300 bg-slate-900 p-2.5 rounded border border-emerald-900/40 overflow-x-auto max-h-40">
            {JSON.stringify(contract.evidence || {}, null, 2)}
          </pre>
        </div>

        {/* 7. Status & Gate Verdict */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">7. EVIDENCE GATE VERDICT</span>
          <div className="text-xs font-mono">
            Verdict: <span className="font-bold text-white">{contract.status === "VERIFIED" ? "GATE_APPROVED" : "GATE_REJECTED / RECOVERING"}</span>
          </div>
          {contract.error_message && (
            <p className="text-xs text-rose-400 mt-1 font-mono">
              Error: {contract.error_message}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
