import React, { useState } from "react";
import { ActionContract, ReviewField } from "../../types";
import { 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  RefreshCw, 
  ExternalLink,
  ShieldCheck,
  Building,
  User,
  GraduationCap,
  Landmark,
  FileCheck2,
  Clock
} from "lucide-react";

interface Step4Props {
  appId: string;
  contracts: ActionContract[];
  reviewFields: ReviewField[];
  portalState: any;
  onProceedToPreview: () => void;
  onBack: () => void;
  loading: boolean;
  executing: boolean;
  onTriggerExecution: () => void;
}

export const Step4FormExecution: React.FC<Step4Props> = ({
  appId,
  contracts,
  reviewFields,
  portalState,
  onProceedToPreview,
  onBack,
  loading,
  executing,
  onTriggerExecution,
}) => {
  const [activeTab, setActiveTab] = useState<"contracts" | "portal">("contracts");

  const personalFields = reviewFields.filter((f) =>
    ["full_name", "date_of_birth", "gender", "category", "email", "phone_number"].includes(f.field_id)
  );
  const academicFields = reviewFields.filter((f) =>
    ["institution_name", "roll_number", "tenth_percentage", "twelfth_percentage"].includes(f.field_id)
  );
  const financialFields = reviewFields.filter((f) =>
    ["annual_family_income", "bank_name", "bank_account_number", "ifsc_code"].includes(f.field_id)
  );

  const allContractsVerified = contracts.length > 0 && contracts.every((c) => c.status === "VERIFIED");

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              Step 4 of 5: Form Auto-Fill & Execution
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              Autonomous Portal Population
            </h1>
            <p className="text-xs text-slate-400">
              Each portal field and enclosure is populated using strict 7-tuple Action Contracts with verified pre/post-conditions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!allContractsVerified && (
              <button
                onClick={onTriggerExecution}
                disabled={executing || loading}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Executing Contracts...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Run / Re-run Auto-Fill</span>
                  </>
                )}
              </button>
            )}

            <div className="flex items-center gap-1 bg-slate-950/80 border border-slate-800 p-1 rounded-lg">
              <button
                onClick={() => setActiveTab("contracts")}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "contracts"
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Action Contracts
              </button>
              <button
                onClick={() => setActiveTab("portal")}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "portal"
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Live Portal DOM View
              </button>
            </div>
          </div>
        </div>
      </div>

      {activeTab === "contracts" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Action Contracts List */}
          <div className="lg:col-span-2 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1 flex items-center justify-between">
              <span>Verified Execution Contracts</span>
              <span className="text-indigo-400 font-mono">
                {contracts.filter((c) => c.status === "VERIFIED").length} / {contracts.length || 7} Completed
              </span>
            </div>

            {contracts.length > 0 ? (
              contracts.map((c, idx) => (
                <div
                  key={c.action_id || idx}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-slate-700 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          c.status === "VERIFIED"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                            : c.status === "FAILED"
                            ? "bg-red-500/20 text-red-400 border border-red-500/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {c.status === "VERIFIED" ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                      </div>
                      <span className="text-sm font-semibold text-white">
                        {c.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                        {c.step_category}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold font-mono ${
                          c.status === "VERIFIED"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-amber-500/20 text-amber-300"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 font-mono bg-slate-950/60 p-2 rounded border border-slate-800/60 truncate">
                    Command: {c.execution_command}
                  </div>

                  {c.attempt > 1 && (
                    <div className="text-[11px] text-amber-400 flex items-center gap-1.5 pt-1">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      <span>Self-Healed via bounded recovery (Attempt #{c.attempt})</span>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm">
                Click "Run / Re-run Auto-Fill" above to begin contract execution.
              </div>
            )}
          </div>

          {/* Right Column: Verified Sections Snapshot */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <User className="w-4 h-4 text-indigo-400" />
                <span>Personal Particulars</span>
              </h3>
              <div className="space-y-2 text-xs">
                {personalFields.map((f) => (
                  <div key={f.field_id} className="flex items-center justify-between pb-1 border-b border-slate-800/60">
                    <span className="text-slate-400">{f.label}</span>
                    <span className="font-semibold text-white font-mono">{f.value || "—"}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-emerald-400" />
                <span>Academic Record</span>
              </h3>
              <div className="space-y-2 text-xs">
                {academicFields.map((f) => (
                  <div key={f.field_id} className="flex items-center justify-between pb-1 border-b border-slate-800/60">
                    <span className="text-slate-400">{f.label}</span>
                    <span className="font-semibold text-white font-mono">{f.value || "—"}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Landmark className="w-4 h-4 text-amber-400" />
                <span>Banking Particulars</span>
              </h3>
              <div className="space-y-2 text-xs">
                {financialFields.map((f) => (
                  <div key={f.field_id} className="flex items-center justify-between pb-1 border-b border-slate-800/60">
                    <span className="text-slate-400">{f.label}</span>
                    <span className="font-semibold text-white font-mono">{f.value || "—"}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Live Simulated Portal View */
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-bold text-white">
                Live Portal DOM Mirror (Simulated Sandbox)
              </span>
            </div>
            <a
              href="http://localhost:8000/portal"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              <span>Open in New Tab</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-inner">
            <div className="bg-slate-900/90 px-4 py-2 border-b border-slate-800 flex items-center gap-2 text-xs text-slate-400 font-mono">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
              <span className="ml-2 text-slate-500">http://localhost:8000/portal/application-form</span>
            </div>

            <div className="p-6 space-y-6">
              <div className="border-b border-slate-800 pb-4">
                <h4 className="text-base font-bold text-white">
                  State Bank of India Foundation — Platinum Jubilee Scholarship
                </h4>
                <p className="text-xs text-slate-400">
                  Application Status: <span className="text-emerald-400 font-semibold">{portalState?.status || "IN_PROGRESS"}</span>
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {reviewFields.map((f) => (
                  <div key={f.field_id} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-[11px] mb-1">{f.label}</div>
                    <div className="text-white font-bold font-mono">{f.value || "—"}</div>
                  </div>
                ))}
              </div>

              <div>
                <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Uploaded Enclosures in Portal
                </h5>
                <div className="flex flex-wrap gap-2">
                  {(portalState?.uploaded_documents || ["doc_aadhaar", "doc_marksheet", "doc_income_cert", "doc_photo"]).map(
                    (d: string) => (
                      <span
                        key={d}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-mono"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{d} [VERIFIED]</span>
                      </span>
                    )
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={onBack}
          disabled={loading || executing}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl border border-slate-700 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Analysis</span>
        </button>

        <button
          onClick={onProceedToPreview}
          disabled={loading || executing}
          className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
        >
          <span>Proceed to Final Submission Preview</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
