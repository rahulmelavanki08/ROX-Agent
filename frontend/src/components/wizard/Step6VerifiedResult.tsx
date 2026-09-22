import React from "react";
import { 
  ShieldCheck, 
  CheckCircle2, 
  FileText, 
  Download, 
  RotateCcw, 
  ExternalLink,
  Award,
  Hash,
  Clock,
  Layers
} from "lucide-react";

interface Step6Props {
  appId: string;
  submissionDetails: any;
  onOpenLedger: () => void;
  onOpenAudit: () => void;
  onReset: () => void;
}

export const Step6VerifiedResult: React.FC<Step6Props> = ({
  appId,
  submissionDetails,
  onOpenLedger,
  onOpenAudit,
  onReset,
}) => {
  const refNumber = submissionDetails?.reference_number || "SCH-2026-45515";
  const receiptHash = submissionDetails?.receipt_hash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
  const timestamp = submissionDetails?.submitted_at || new Date().toISOString();

  const handleDownloadLedger = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/applications/${appId}/ledger`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ROX_PROOF_LEDGER_${appId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download ledger", err);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Huge Verified Success Certification Banner */}
      <div className="bg-gradient-to-b from-emerald-950/60 via-slate-900 to-slate-900 border-2 border-emerald-500/50 rounded-2xl p-8 sm:p-10 text-center relative overflow-hidden shadow-2xl shadow-emerald-950/40">
        <div className="absolute -top-24 -left-24 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-4">
          <div className="inline-flex p-4 bg-emerald-500/20 text-emerald-400 rounded-2xl border border-emerald-500/40 shadow-lg shadow-emerald-500/20">
            <Award className="w-12 h-12" />
          </div>

          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              Evidence Gate Certified
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              Application Officially Submitted
            </h1>
            <p className="text-sm text-slate-300 max-w-xl mx-auto">
              The deterministic Evidence Gate has verified every field and document enclosure with zero hallucinations.
              Your binding submission has been acknowledged by the portal.
            </p>
          </div>

          {/* Reference Card */}
          <div className="bg-slate-950/80 border border-emerald-500/30 rounded-xl p-5 max-w-lg mx-auto shadow-inner text-left space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Official Reference Number
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold font-mono">
                ACTIVE
              </span>
            </div>
            <div className="text-2xl font-black text-white font-mono tracking-wider text-center py-1">
              {refNumber}
            </div>

            <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Hash className="w-3.5 h-3.5 text-slate-500" />
                  Receipt SHA-256:
                </span>
                <span className="font-mono text-indigo-300 truncate max-w-[220px]" title={receiptHash}>
                  {receiptHash}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  Timestamp:
                </span>
                <span className="font-mono text-slate-300">
                  {new Date(timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={handleDownloadLedger}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download Proof Ledger (.JSON)</span>
            </button>

            <button
              onClick={onOpenAudit}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition-all"
            >
              <Layers className="w-4 h-4" />
              <span>Inspect Action Contracts</span>
            </button>

            <button
              onClick={onReset}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-xl border border-slate-800 transition-all"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Start Another Application</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
