import React from "react";
import { ApplicationTypeItem } from "../../types";
import { GraduationCap, Building2, FileCheck2, ShieldCheck, ArrowRight, Calendar, AlertCircle, FileText } from "lucide-react";

interface Step1Props {
  types: ApplicationTypeItem[];
  selectedTypeId: string;
  onSelectType: (id: string) => void;
  onProceed: () => void;
  loading: boolean;
}

export const Step1SelectApplication: React.FC<Step1Props> = ({
  types,
  selectedTypeId,
  onSelectType,
  onProceed,
  loading,
}) => {
  const currentApp = types.find((t) => t.id === selectedTypeId) || types[0];

  const getIcon = (id: string) => {
    switch (id) {
      case "scholarship_sbi":
        return <GraduationCap className="w-6 h-6 text-indigo-400" />;
      case "hostel_post_matric":
        return <Building2 className="w-6 h-6 text-emerald-400" />;
      case "certificate_income_caste":
        return <FileCheck2 className="w-6 h-6 text-amber-400" />;
      default:
        return <FileText className="w-6 h-6 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-900/40 rounded-xl p-6 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-indigo-500/5 blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-3">
            <ShieldCheck className="w-3.5 h-3.5" />
            Step 1 of 5: Application Discovery
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Select Target Application & Portal Scheme
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            Choose the application you wish ROX to complete. ROX autonomously parses portal schema rules,
            extracts machine-checkable evidence from your documents, recovers from file format mismatches,
            and proves execution through a tamper-evident cryptographic ledger.
          </p>
        </div>
      </div>

      {/* Main Selection Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Dropdown and Quick Cards */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Application Type (Select Scheme)
            </label>
            <select
              value={selectedTypeId}
              onChange={(e) => onSelectType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium cursor-pointer"
            >
              {types.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Available Application Schemas
            </div>
            {types.map((t) => {
              const isSelected = t.id === selectedTypeId;
              return (
                <button
                  key={t.id}
                  onClick={() => onSelectType(t.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 shadow-md shadow-indigo-950/50"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-slate-800/80 rounded-lg shrink-0 mt-0.5">
                      {getIcon(t.id)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-xs font-semibold text-white truncate">
                          {t.title}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-medium whitespace-nowrap">
                          {t.badge}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {t.authority}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Scheme Deep-Dive Preview */}
        {currentApp && (
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                    {getIcon(currentApp.id)}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">
                      {currentApp.title}
                    </h2>
                    <p className="text-xs text-slate-400">
                      Issuing Authority: <span className="text-slate-200">{currentApp.authority}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg shrink-0">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Deadline: {currentApp.deadline}</span>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Scheme Scope & Description
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  {currentApp.description}
                </p>
              </div>

              {/* Required Documents Checklist Preview */}
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
                  <span>Mandatory Documents Required by Portal</span>
                  <span className="text-[11px] text-indigo-400 font-normal">
                    {currentApp.required_documents.length} Enclosures
                  </span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {currentApp.required_documents.map((doc, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-lg space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">
                          {doc.name}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                          {doc.accepted_formats.join(", ")}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-normal">
                        {doc.description}
                      </p>
                      <div className="text-[10px] text-slate-500 flex items-center gap-2 pt-1 border-t border-slate-800/60">
                        <span>Max: {doc.max_size_kb >= 1024 ? `${doc.max_size_kb / 1024} MB` : `${doc.max_size_kb} KB`}</span>
                        {doc.dimensions && (
                          <span>• Dims: {doc.dimensions[0]}x{doc.dimensions[1]} px</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Self-Healing Benchmark Notice for Primary Scholarship */}
              {currentApp.id === "scholarship_sbi" && (
                <div className="bg-amber-950/20 border border-amber-900/40 rounded-lg p-3.5 text-xs text-amber-300/90 flex items-start gap-3">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-semibold text-amber-200">
                      Hackathon Track A1 Built-in Scenarios:
                    </span>
                    <p className="text-amber-300/80 text-[11px] leading-relaxed">
                      The SBI Platinum Jubilee dataset contains intentional realistic edge cases:
                      oversized 5.7 MB income certificate, 1600x1200 PNG photograph, and Aadhaar vs Marksheet DOB conflict.
                      ROX will analyze these and self-heal them in Step 3!
                    </p>
                  </div>
                </div>
              )}

              {/* Proceed Button */}
              <div className="pt-2 flex justify-end">
                <button
                  onClick={onProceed}
                  disabled={loading}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
                >
                  <span>{loading ? "Initializing..." : "Continue to Document Upload"}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
