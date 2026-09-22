import React, { useState } from "react";
import { AlertTriangle, ShieldCheck, Check, ArrowRight } from "lucide-react";
import { ConflictReport } from "../types";

interface ConflictResolutionModalProps {
  conflict: ConflictReport | null;
  onResolve: (fieldId: string, chosenValue: string, source: string) => void;
  isOpen: boolean;
}

export const ConflictResolutionModal: React.FC<ConflictResolutionModalProps> = ({
  conflict,
  onResolve,
  isOpen
}) => {
  if (!isOpen || !conflict) return null;

  const [selectedValue, setSelectedValue] = useState<string>(conflict.candidates[0]?.value || "");
  const [selectedSource, setSelectedSource] = useState<string>(conflict.candidates[0]?.source_file || "");

  const handleSelect = (val: string, src: string) => {
    setSelectedValue(val);
    setSelectedSource(src);
  };

  const handleConfirm = () => {
    onResolve(conflict.field_id, selectedValue, selectedSource);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-rose-500/50 rounded-2xl max-w-xl w-full p-6 shadow-2xl shadow-rose-950/50">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <span>ZERO-TRUST CONFLICT GATE:</span>
              <span className="text-rose-400 font-mono uppercase">{conflict.field_label}</span>
            </h3>
            <p className="text-xs text-slate-400">
              Discrepancy detected across official documents. Autonomous decision blocked.
            </p>
          </div>
        </div>

        <div className="bg-rose-950/20 border border-rose-900/40 rounded-xl p-3.5 mb-5 text-xs text-rose-200/90 leading-relaxed">
          {conflict.blocking_reason}
        </div>

        <div className="space-y-3 mb-6">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Candidate Values Extracted from Documents:
          </label>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {conflict.candidates.map((cand, idx) => {
              const isSelected = selectedValue === cand.value;
              return (
                <div
                  key={idx}
                  onClick={() => handleSelect(cand.value, cand.source_file)}
                  className={`p-4 rounded-xl border cursor-pointer transition relative ${
                    isSelected
                      ? "bg-blue-950/50 border-blue-500 shadow-lg shadow-blue-500/20"
                      : "bg-slate-850 hover:bg-slate-800 border-slate-750 text-slate-400"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[11px] font-mono text-slate-400 font-semibold truncate max-w-[150px]">
                      {cand.source_file}
                    </span>
                    {isSelected && <Check className="w-4 h-4 text-blue-400" />}
                  </div>

                  <div className="text-xl font-mono font-bold text-white mb-2">
                    {cand.value}
                  </div>

                  <div className="text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded border border-slate-800 font-mono">
                    "{cand.evidence_text}"
                  </div>

                  <div className="mt-2 text-[10px] text-slate-500 flex justify-between">
                    <span>Page {cand.source_page}</span>
                    <span>Conf: {(cand.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <div className="text-xs text-slate-500">
            Selected: <span className="font-mono text-white font-bold">{selectedValue}</span> ({selectedSource})
          </div>
          <button
            onClick={handleConfirm}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center space-x-2 shadow-lg shadow-blue-600/30 transition"
          >
            <span>Resolve & Unblock Execution</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
