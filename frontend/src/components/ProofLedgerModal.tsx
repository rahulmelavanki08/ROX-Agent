import React from "react";
import { X, ShieldCheck, Download, Hash, Clock, User, CheckCircle2, AlertCircle } from "lucide-react";
import { LedgerEntry } from "../types";

interface ProofLedgerModalProps {
  entries: LedgerEntry[];
  appId: string;
  onClose: () => void;
  isOpen: boolean;
}

export const ProofLedgerModal: React.FC<ProofLedgerModalProps> = ({
  entries,
  appId,
  onClose,
  isOpen
}) => {
  if (!isOpen) return null;

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(entries, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `rox-evidence-ledger-${appId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-6 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <span>Cryptographic Proof Ledger</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  SHA-256 Hash Chained
                </span>
              </h3>
              <p className="text-xs text-slate-400">Append-only audit trail guaranteeing machine-verifiable provenance</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleExportJSON}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-indigo-600/20 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Ledger (.JSON)</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Ledger Entries List */}
        <div className="overflow-y-auto my-4 space-y-3 pr-2 flex-1 font-mono text-xs">
          {entries.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              No ledger records generated yet.
            </div>
          ) : (
            entries.map((entry, index) => (
              <div
                key={index}
                className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-blue-400">{entry.step_id}</span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center space-x-1 text-slate-300">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{entry.formatted_time || "00:00:00"}</span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center space-x-1 text-indigo-400">
                      <User className="w-3 h-3" />
                      <span>{entry.actor}</span>
                    </span>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                      entry.status === "VERIFIED" || entry.status === "VERIFIED_SUCCESS" || entry.status === "PASSED"
                        ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                        : entry.status === "FAILED"
                        ? "bg-rose-950 text-rose-300 border-rose-800"
                        : "bg-amber-950 text-amber-300 border-amber-800"
                    }`}
                  >
                    {entry.status}
                  </span>
                </div>

                <div className="text-sm font-semibold text-white mb-2">{entry.action}</div>

                {entry.evidence && (
                  <div className="bg-slate-900/90 p-2.5 rounded border border-slate-800 text-[11px] text-slate-300 overflow-x-auto max-h-32 mb-2">
                    <pre>{JSON.stringify(entry.evidence, null, 2)}</pre>
                  </div>
                )}

                <div className="flex items-center space-x-2 text-[10px] text-slate-500 truncate pt-1 border-t border-slate-900">
                  <Hash className="w-3 h-3 text-slate-600 shrink-0" />
                  <span className="truncate">Hash: {entry.entry_hash || "0".repeat(64)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
