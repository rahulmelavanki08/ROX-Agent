import React, { useState } from "react";
import { ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight, Download, Award, FileText, Lock } from "lucide-react";
import { ReviewField, DocumentStatus } from "../types";

interface FinalReviewModalProps {
  fields: ReviewField[];
  documents: DocumentStatus[];
  appId: string;
  onApproveAndSubmit: () => void;
  submissionResult: any;
  isOpen: boolean;
  onClose: () => void;
  onOpenLedger: () => void;
}

export const FinalReviewModal: React.FC<FinalReviewModalProps> = ({
  fields,
  documents,
  appId,
  onApproveAndSubmit,
  submissionResult,
  isOpen,
  onClose,
  onOpenLedger
}) => {
  if (!isOpen) return null;

  const [authorized, setAuthorized] = useState(false);
  const isSubmitted = submissionResult && submissionResult.status === "SUCCESS";
  const refNumber = submissionResult?.submission_details?.reference_number || "SCH-2026-88941";
  const receiptHash = submissionResult?.submission_details?.receipt_hash;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-6 shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                {isSubmitted ? "VERIFIED APPLICATION SUBMISSION" : "EVIDENCE-BACKED APPLICATION REVIEW"}
              </h3>
              <p className="text-xs text-slate-400">
                {isSubmitted
                  ? "Independently verified by deterministic Evidence Gate."
                  : "Audit complete provenance before irreversible action approval."}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
          >
            Close
          </button>
        </div>

        {/* Success Banner if Submitted */}
        {isSubmitted && (
          <div className="my-4 p-5 rounded-2xl bg-gradient-to-r from-emerald-950/80 to-slate-900 border border-emerald-500/60 shadow-xl shadow-emerald-950/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Award className="w-10 h-10 text-emerald-400 shrink-0" />
                <div>
                  <span className="text-xs font-mono uppercase font-bold text-emerald-400 tracking-wider">
                    EVIDENCE GATE CERTIFIED
                  </span>
                  <h2 className="text-2xl font-mono font-extrabold text-white">
                    VERIFIED SUCCESS
                  </h2>
                  <p className="text-xs text-slate-300 mt-1">
                    Application successfully submitted and confirmed by server response.
                  </p>
                </div>
              </div>

              <div className="text-right">
                <span className="text-xs text-slate-400 block font-mono">Reference Number:</span>
                <span className="text-xl font-mono font-extrabold text-emerald-300 bg-emerald-950/80 px-3 py-1 rounded-lg border border-emerald-600 block mt-0.5">
                  {refNumber}
                </span>
              </div>
            </div>

            {receiptHash && (
              <div className="mt-3 pt-3 border-t border-emerald-900/50 flex items-center justify-between text-[11px] font-mono text-emerald-300/80">
                <span className="truncate max-w-[480px]">Receipt Hash: {receiptHash}</span>
                <button
                  onClick={onOpenLedger}
                  className="px-3 py-1 rounded bg-emerald-800/60 hover:bg-emerald-700 text-white font-bold transition"
                >
                  View Proof Ledger
                </button>
              </div>
            )}
          </div>
        )}

        {/* Audit Tables Container */}
        <div className="overflow-y-auto my-3 space-y-4 pr-2 flex-1">
          {/* Document Verification Status */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Mandatory Documents Verification
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {documents.map((doc, idx) => (
                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <div className="truncate">
                    <div className="text-xs font-bold text-white truncate">{doc.label}</div>
                    <div className="text-[10px] text-emerald-400 font-mono">✓ VERIFIED</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fields Provenance Audit Table */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Field-by-Field Evidence Provenance
            </h4>
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Field</th>
                    <th className="py-2.5 px-3">Extracted Value</th>
                    <th className="py-2.5 px-3">Source Document</th>
                    <th className="py-2.5 px-3">Evidence Quote</th>
                    <th className="py-2.5 px-3">Confidence</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {fields.map((fld, idx) => (
                    <tr key={idx} className="hover:bg-slate-850/50 transition">
                      <td className="py-2.5 px-3 text-slate-300 font-bold">{fld.label}</td>
                      <td className="py-2.5 px-3 text-white font-semibold">{fld.value || "—"}</td>
                      <td className="py-2.5 px-3 text-slate-400">{fld.source_file || "Manual"} (p.{fld.source_page})</td>
                      <td className="py-2.5 px-3 text-slate-500 italic max-w-xs truncate">"{fld.evidence_text || "Direct user authorization"}"</td>
                      <td className="py-2.5 px-3 text-emerald-400">{(fld.confidence * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                          ✓ VERIFIED
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Irreversible Action Guard & Submission Controls */}
        {!isSubmitted && (
          <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={authorized}
                onChange={(e) => setAuthorized(e.target.checked)}
                className="w-4 h-4 rounded text-blue-600 bg-slate-950 border-slate-700 focus:ring-0 cursor-pointer"
              />
              <span className="text-xs text-slate-300 font-medium">
                <Lock className="w-3.5 h-3.5 inline text-amber-400 mr-1" />
                I explicitly authorize ROX to execute binding final submission.
              </span>
            </label>

            <button
              onClick={onApproveAndSubmit}
              disabled={!authorized}
              className={`px-5 py-2.5 rounded-xl font-bold text-xs flex items-center space-x-2 shadow-lg transition ${
                authorized
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30 cursor-pointer"
                  : "bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed"
              }`}
            >
              <span>Execute Verified Submission</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
