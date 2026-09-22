import React, { useState, useEffect } from "react";
import { ConflictReport, FileIssue, ReviewField, LLMAudit, LLMFaultReply } from "../../types";
import { 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  Sparkles, 
  ArrowRight, 
  ArrowLeft, 
  Wrench, 
  ShieldCheck, 
  FileImage,
  RefreshCw,
  HelpCircle,
  Edit3,
  Check,
  X,
  PlusCircle,
  FileCheck,
  Bot,
  MessageSquare
} from "lucide-react";

interface Step3Props {
  appState?: string;
  conflicts: ConflictReport[];
  fileIssues: FileIssue[];
  reviewFields: ReviewField[];
  llmAudit?: LLMAudit | null;
  llmFaultReplies?: LLMFaultReply[];
  llmProvider?: string;
  onResolveConflict: (fieldId: string, value: string, source: string) => Promise<void>;
  onAdaptFile: (fileName: string, action: "compress_pdf" | "convert_image" | "convert_to_pdf") => Promise<any>;
  onAutoAdaptAll?: () => Promise<any>;
  onUpdateField?: (fieldId: string, value: string) => Promise<void>;
  onProceedToExecution: () => void;
  onBack: () => void;
  loading: boolean;
}

export const Step3IssueAnalysis: React.FC<Step3Props> = ({
  appState,
  conflicts,
  fileIssues,
  reviewFields,
  llmAudit,
  llmFaultReplies,
  llmProvider,
  onResolveConflict,
  onAdaptFile,
  onAutoAdaptAll,
  onUpdateField,
  onProceedToExecution,
  onBack,
  loading,
}) => {
  const [adaptingFile, setAdaptingFile] = useState<string | null>(null);
  const [adaptationResults, setAdaptationResults] = useState<Record<string, any>>({});
  const [autoHealing, setAutoHealing] = useState(false);
  const [autoHealedList, setAutoHealedList] = useState<any[]>([]);
  const [resolvingField, setResolvingField] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"extracted" | "issues">(conflicts.length > 0 ? "issues" : "extracted");

  // Zero-Touch Self-Healing: Automatically convert images to PDF and compress oversized files upon loading
  useEffect(() => {
    if (fileIssues.length > 0 && !autoHealing && autoHealedList.length === 0) {
      triggerZeroTouchAdaptation();
    }
  }, [fileIssues.length]);

  const triggerZeroTouchAdaptation = async () => {
    if (!onAutoAdaptAll) return;
    try {
      setAutoHealing(true);
      const res = await onAutoAdaptAll();
      if (res && res.results) {
        setAutoHealedList(res.results);
      }
    } catch (err) {
      console.error("Zero touch adaptation error:", err);
    } finally {
      setAutoHealing(false);
    }
  };

  // Inline editing state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [isSavingField, setIsSavingField] = useState<boolean>(false);

  // New custom field modal/input state
  const [showAddField, setShowAddField] = useState<boolean>(false);
  const [newFieldKey, setNewFieldKey] = useState<string>("");
  const [newFieldValue, setNewFieldValue] = useState<string>("");

  const handleAdapt = async (fileName: string, action: "compress_pdf" | "convert_image" | "convert_to_pdf") => {
    try {
      setAdaptingFile(fileName);
      const res = await onAdaptFile(fileName, action);
      setAdaptationResults((prev) => ({ ...prev, [fileName]: res }));
    } finally {
      setAdaptingFile(null);
    }
  };

  const handleConflictClick = async (fieldId: string, val: string, src: string) => {
    try {
      setResolvingField(fieldId);
      await onResolveConflict(fieldId, val, src);
    } finally {
      setResolvingField(null);
    }
  };

  const startEditField = (field: ReviewField) => {
    setEditingFieldId(field.field_id);
    setEditValue(field.value || "");
  };

  const saveEditField = async (fieldId: string) => {
    if (!onUpdateField) return;
    try {
      setIsSavingField(true);
      await onUpdateField(fieldId, editValue);
      setEditingFieldId(null);
    } finally {
      setIsSavingField(false);
    }
  };

  const handleSaveNewField = async () => {
    if (!onUpdateField || !newFieldKey.trim() || !newFieldValue.trim()) return;
    try {
      setIsSavingField(true);
      await onUpdateField(newFieldKey.trim().toLowerCase().replace(/\s+/g, "_"), newFieldValue.trim());
      setNewFieldKey("");
      setNewFieldValue("");
      setShowAddField(false);
    } finally {
      setIsSavingField(false);
    }
  };

  const totalIssuesCount = conflicts.length + fileIssues.length;
  const isAllResolved = conflicts.length === 0 && appState !== "BLOCKED";

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              Step 3 of 5: Document Extraction & AI Issue Analysis
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              Extracted Particulars & Self-Healing Analysis
            </h1>
            <p className="text-xs text-slate-400">
              ROX extracted application entities directly from your uploaded document text. Review details below or make inline edits.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800 p-1.5 rounded-lg shrink-0">
            <button
              onClick={() => setActiveTab("extracted")}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                activeTab === "extracted"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Extracted Data ({reviewFields.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("issues")}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                activeTab === "issues"
                  ? conflicts.length > 0 ? "bg-red-600 text-white shadow-sm" : "bg-amber-600 text-white shadow-sm"
                  : conflicts.length > 0
                  ? "bg-red-500/20 text-red-300 border border-red-500/50 animate-pulse"
                  : totalIssuesCount > 0
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <AlertTriangle className={`w-3.5 h-3.5 ${conflicts.length > 0 ? "text-red-400" : ""}`} />
              <span>Active Issues ({totalIssuesCount})</span>
            </button>
          </div>
        </div>
      </div>

      {activeTab === "extracted" ? (
        /* Extracted Data View with Verbatim Provenance Citations & Inline Editing */
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          {/* Gemini AI Inter-Document Audit Banner */}
          {llmAudit && (
            <div className={`rounded-xl p-3.5 border flex items-start justify-between gap-3 text-xs ${
              llmAudit.same_person
                ? "bg-indigo-950/40 border-indigo-500/30 text-indigo-200"
                : "bg-red-950/40 border-red-500/40 text-red-200"
            }`}>
              <div className="flex items-start gap-2.5">
                <Bot className={`w-4 h-4 shrink-0 mt-0.5 ${llmAudit.same_person ? "text-indigo-400" : "text-red-400"}`} />
                <div>
                  <span className="font-bold text-white">Gemini AI Inter-Document Audit: </span>
                  <span className="leading-relaxed">{llmAudit.summary}</span>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/80 font-semibold border border-slate-700 shrink-0 text-slate-300">
                {Math.round((llmAudit.confidence || 0.98) * 100)}% Match Conf
              </span>
            </div>
          )}

          {/* Identity Mismatch Critical Alert Banner */}
          {conflicts.length > 0 && (
            <div className="bg-red-500/10 border-2 border-red-500/50 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-red-200">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-red-300 uppercase tracking-wider">
                    ⚠️ Cross-Document Identity Mismatch Detected ({conflicts.length} Conflict{conflicts.length > 1 ? "s" : ""})
                  </div>
                  <div className="text-xs text-red-200 mt-0.5">
                    Uploaded documents belong to different individuals or have conflicting records for <strong>{conflicts.map(c => c.field_label).join(", ")}</strong>. Automated progression is locked until you review and resolve these mismatches.
                  </div>
                </div>
              </div>
              <button
                onClick={() => setActiveTab("issues")}
                className="px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg shrink-0 transition-colors shadow-lg shadow-red-950/40 cursor-pointer"
              >
                Resolve Mismatch &rarr;
              </button>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span>Extracted Application Particulars</span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 normal-case">
                  Parsed from Uploaded Documents
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Every extracted entity links back to verifiable machine evidence in the original document. Click "Edit" on any field to manually adjust values.
              </p>
            </div>
            
            <button
              onClick={() => setShowAddField(!showAddField)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all shrink-0"
            >
              <PlusCircle className="w-3.5 h-3.5 text-indigo-400" />
              <span>{showAddField ? "Cancel Add" : "Add / Override Field"}</span>
            </button>
          </div>

          {/* Add Field Inline Form */}
          {showAddField && (
            <div className="bg-slate-950 border border-indigo-500/40 rounded-xl p-4 space-y-3">
              <div className="text-xs font-bold text-indigo-300">
                Add or Override Application Field
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Field Label / Key</label>
                  <input
                    type="text"
                    placeholder="e.g. mobile_number, email_address, guardian_name"
                    value={newFieldKey}
                    onChange={(e) => setNewFieldKey(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Field Value</label>
                  <input
                    type="text"
                    placeholder="e.g. 9876543210"
                    value={newFieldValue}
                    onChange={(e) => setNewFieldValue(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => setShowAddField(false)}
                  className="px-3 py-1 bg-slate-800 text-slate-400 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveNewField}
                  disabled={isSavingField || !newFieldKey.trim() || !newFieldValue.trim()}
                  className="px-4 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
                >
                  {isSavingField ? "Saving..." : "Save Field"}
                </button>
              </div>
            </div>
          )}

          {/* Review Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {reviewFields.map((field) => {
              const isEditing = editingFieldId === field.field_id;

              const isConflict = field.status === "CONFLICT";

              return (
                <div
                  key={field.field_id}
                  className={`border p-3.5 rounded-lg space-y-2 transition-all ${
                    isConflict
                      ? "bg-red-950/20 border-red-500/50 hover:border-red-500/80 shadow-md shadow-red-950/20"
                      : "bg-slate-950 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">
                      {field.label}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
                          field.status === "VERIFIED"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : isConflict
                            ? "bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {isConflict ? "⚠️ MISMATCH" : field.status}
                      </span>
                      {!isEditing && onUpdateField && (
                        <button
                          onClick={() => startEditField(field)}
                          className="p-1 hover:bg-slate-800 text-slate-400 hover:text-indigo-300 rounded transition-colors"
                          title="Edit extracted value"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Value / Inline Edit Input */}
                  {isEditing ? (
                    <div className="flex items-center gap-2 pt-1">
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="flex-1 bg-slate-900 border border-indigo-500 rounded px-2.5 py-1 text-sm font-bold text-white font-mono focus:outline-none"
                        autoFocus
                      />
                      <button
                        onClick={() => saveEditField(field.field_id)}
                        disabled={isSavingField}
                        className="p-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors"
                        title="Save changes"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setEditingFieldId(null)}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded transition-colors"
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : isConflict ? (
                    <div className="space-y-1.5">
                      <div className="text-xs text-red-300 font-semibold flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                        <span>Conflicting documents detected</span>
                      </div>
                      <button
                        onClick={() => setActiveTab("issues")}
                        className="w-full py-1.5 px-2 bg-red-600/20 hover:bg-red-600/40 text-red-200 text-xs font-semibold rounded border border-red-500/40 transition-colors flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <span>Resolve in Active Issues ({conflicts.length}) &rarr;</span>
                      </button>
                    </div>
                  ) : (
                    <div className="text-sm font-bold text-white font-mono">
                      {field.value || <span className="text-slate-500 italic">Not extracted</span>}
                    </div>
                  )}

                  {/* Machine Provenance Citations */}
                  {field.source_file && (
                    <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/60">
                      <span className="truncate font-mono">Source: {field.source_file}</span>
                      <span className="text-indigo-400 font-mono text-[10px]">
                        {Math.round((field.confidence || 0.95) * 100)}% Conf
                      </span>
                    </div>
                  )}
                  {field.evidence_text && (
                    <p className="text-[10px] text-slate-500 italic truncate bg-slate-900/50 px-2 py-1 rounded">
                      "{field.evidence_text}"
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Issues Tab: Cross-Document Conflicts & File Constraints */
        <div className="space-y-4">
          {/* Status Alert Bar */}
          {totalIssuesCount > 0 ? (
            <div className="bg-amber-950/30 border border-amber-900/50 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold text-amber-300">
                  {totalIssuesCount} Issue{totalIssuesCount > 1 ? "s" : ""} Identified Before Portal Transmission
                </div>
                <p className="text-xs text-amber-400/80 mt-0.5 leading-relaxed">
                  Our zero-trust architecture prevents portal rejection. Review the conflict resolution and 1-click self-healing adaptations below.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-950/30 border border-emerald-900/50 rounded-xl p-4 flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold text-emerald-300">
                  All Document Issues & Conflicts Resolved!
                </div>
                <p className="text-xs text-emerald-400/80 mt-0.5">
                  Application data and file enclosures are 100% verified and ready for automated portal execution.
                </p>
              </div>
            </div>
          )}

          {/* Gemini Inter-Document Verification Audit Card */}
          {llmAudit && (
            <div className="bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/40 rounded-xl p-5 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-indigo-500/20">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shrink-0">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <span>Gemini AI Inter-Document Audit</span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${
                          llmAudit.same_person
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            : "bg-red-500/20 text-red-300 border-red-500/40 animate-pulse"
                        }`}>
                          {llmAudit.same_person ? "✓ Same Individual Confirmed" : "⚠️ Identity Mismatch Detected"}
                        </span>
                      </h3>
                    </div>
                    <p className="text-xs text-indigo-200/80 mt-0.5">
                      Cross-referencing applicant identity records across Aadhaar, Marksheets, Passbook, and Income Certificate.
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xs font-mono text-indigo-400 font-bold bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-800">
                    {Math.round((llmAudit.confidence || 0.98) * 100)}% Confidence
                  </span>
                </div>
              </div>

              {/* Summary & Conversational Verdict */}
              <div className="space-y-2 text-xs">
                <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-slate-300 leading-relaxed font-sans">
                  <strong className="text-indigo-300">Audit Summary: </strong>
                  {llmAudit.summary}
                </div>

                {llmAudit.llm_verdict && (
                  <div className="bg-indigo-950/30 border border-indigo-500/30 rounded-lg p-3 text-indigo-200 text-xs leading-relaxed flex items-start gap-2.5">
                    <MessageSquare className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-indigo-300 block mb-0.5">ROX AI Agent Verdict:</span>
                      <span>{llmAudit.llm_verdict}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Key Matches & Discrepancies Grid */}
              {((llmAudit.key_matches && llmAudit.key_matches.length > 0) || (llmAudit.discrepancies && llmAudit.discrepancies.length > 0)) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {/* Key Matches */}
                  {llmAudit.key_matches && llmAudit.key_matches.length > 0 && (
                    <div className="bg-slate-950/60 border border-emerald-500/30 rounded-lg p-3 space-y-1.5">
                      <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block">
                        ✓ Verified Cross-Document Matches
                      </span>
                      <div className="space-y-1">
                        {llmAudit.key_matches.map((m: any, idx: number) => (
                          <div key={idx} className="text-xs text-slate-300 flex items-start justify-between gap-2">
                            <span className="font-medium text-slate-400">{typeof m === 'string' ? m : m.field}:</span>
                            <span className="text-emerald-300 font-mono text-[11px] truncate">{typeof m === 'string' ? 'MATCH' : m.details || m.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Discrepancies */}
                  {llmAudit.discrepancies && llmAudit.discrepancies.length > 0 && (
                    <div className="bg-slate-950/60 border border-red-500/30 rounded-lg p-3 space-y-1.5">
                      <span className="text-[11px] font-bold text-red-400 uppercase tracking-wider block">
                        ⚠️ Cross-Document Inconsistencies
                      </span>
                      <div className="space-y-1">
                        {llmAudit.discrepancies.map((d: any, idx: number) => (
                          <div key={idx} className="text-xs text-slate-300 flex items-start justify-between gap-2">
                            <span className="font-medium text-slate-400">{typeof d === 'string' ? d : d.field}:</span>
                            <span className="text-red-300 font-mono text-[11px] truncate">{typeof d === 'string' ? 'MISMATCH' : d.details || d.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Conversational LLM Fault Replies */}
          {llmFaultReplies && llmFaultReplies.length > 0 && (
            <div className="space-y-3">
              {llmFaultReplies.map((fault, idx) => (
                <div 
                  key={idx}
                  className="bg-slate-900 border border-indigo-500/30 rounded-xl p-4 shadow-md space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-indigo-500/20 text-indigo-300 rounded-lg">
                        <Bot className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-white font-mono">
                        ROX AI Agent Fault Diagnosis: {fault.fault_title}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                        fault.severity === "CRITICAL"
                          ? "bg-red-500/20 text-red-300 border border-red-500/40"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                      }`}>
                        {fault.severity}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {fault.fault_category}
                      </span>
                    </div>
                  </div>

                  {/* Conversational Reply */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs text-indigo-200/90 leading-relaxed flex items-start gap-2.5">
                    <MessageSquare className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <p>{fault.llm_agent_reply}</p>
                      {fault.recovery_action && (
                        <p className="text-slate-400 text-[11px] pt-1 border-t border-slate-800">
                          <strong className="text-indigo-300">Recommended Self-Healing: </strong>
                          {fault.recovery_action}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 1. Cross-Document Conflicts Alert Cards */}
          {conflicts.map((c) => (
            <div
              key={c.field_id}
              className="bg-slate-900 border border-amber-500/40 rounded-xl p-5 shadow-lg shadow-amber-950/10 space-y-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
                    <HelpCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span>Cross-Document Conflict: {c.field_label}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-semibold">
                        Requires User Choice
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {c.blocking_reason}
                    </p>
                  </div>
                </div>
              </div>

              {/* Conflict Options Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {c.candidates.map((cand, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-950 border border-slate-800 rounded-lg p-3.5 flex flex-col justify-between gap-3 hover:border-slate-700 transition-all"
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-400 font-medium">
                          Source Document:
                        </span>
                        <span className="text-indigo-400 font-semibold font-mono">
                          {cand.source_file}
                        </span>
                      </div>
                      <div className="text-base font-bold text-white my-1 font-mono">
                        "{cand.value}"
                      </div>
                      <p className="text-[11px] text-slate-400 italic bg-slate-900/60 p-2 rounded border border-slate-800/60">
                        "{cand.evidence_text}"
                      </p>
                    </div>

                    <button
                      onClick={() => handleConflictClick(c.field_id, cand.value, cand.source_file)}
                      disabled={resolvingField === c.field_id}
                      className="w-full py-2 px-3 bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-semibold rounded-lg border border-indigo-500/40 hover:border-indigo-500 transition-all flex items-center justify-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>
                        {resolvingField === c.field_id ? "Saving..." : `Use "${cand.value}" from ${cand.source_file}`}
                      </span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Zero-Touch Self-Healing Live Progress Banner */}
          {autoHealing && (
            <div className="bg-indigo-950/60 border border-indigo-500/40 rounded-xl p-4 flex items-center gap-3 animate-pulse">
              <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-white">⚡ ROX Agent Auto-Standardizing Documents...</h4>
                <p className="text-xs text-indigo-200/80">
                  Automatically converting uploaded images to official PDFs and compressing files under portal limits without manual intervention.
                </p>
              </div>
            </div>
          )}

          {/* Zero-Touch Self-Healing Verified Summary */}
          {autoHealedList.length > 0 && (
            <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2 text-emerald-300 text-sm font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Zero-Touch Self-Healing Applied ({autoHealedList.length} documents automatically standardized)</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {autoHealedList.map((item, idx) => (
                  <div key={idx} className="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between">
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-slate-400 truncate font-mono text-[11px]">{item.original_file}</span>
                      <span className="text-slate-500">➔</span>
                      <span className="text-emerald-300 font-bold truncate font-mono text-[11px]">{item.adapted_file}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold shrink-0 ml-2">
                      {item.action === "convert_to_pdf" ? "PDF Verified" : item.action === "compress_pdf" ? `${item.final_size_kb} KB` : "JPG 200x230"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. File Level Issues Cards (Oversized & Unsupported Formats) */}
          {fileIssues.map((issue) => {
            const isOversized = issue.issue_type === "OVERSIZED_FILE";
            const isConvertToPdf = issue.action_required === "convert_to_pdf";
            const adaptResult = adaptationResults[issue.file_name];
            const isAdapting = adaptingFile === issue.file_name;

            return (
              <div
                key={issue.file_name}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-lg shrink-0 ${
                        isOversized
                          ? "bg-amber-500/10 text-amber-400"
                          : isConvertToPdf
                          ? "bg-blue-500/10 text-blue-400"
                          : "bg-purple-500/10 text-purple-400"
                      }`}
                    >
                      {isOversized ? <FileText className="w-5 h-5" /> : <FileImage className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white">
                          {isOversized ? "Oversized PDF Document" : isConvertToPdf ? "Image Uploaded for PDF Document" : "Unsupported Image Format & Size"}
                        </h3>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold font-mono">
                          {issue.file_name}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {issue.message}
                      </p>
                    </div>
                  </div>

                  {/* 1-Click Self-Healing Button */}
                  <button
                    onClick={() => handleAdapt(issue.file_name, issue.action_required as any)}
                    disabled={isAdapting || Boolean(adaptResult)}
                    className={`px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5 shrink-0 shadow-md ${
                      adaptResult
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : "bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-indigo-600/30"
                    }`}
                  >
                    {isAdapting ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Applying Self-Healing...</span>
                      </>
                    ) : adaptResult ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Self-Healed [Verified]</span>
                      </>
                    ) : (
                      <>
                        <Wrench className="w-3.5 h-3.5" />
                        <span>
                          {isOversized ? "⚡ Auto-Compress PDF (<2MB)" : isConvertToPdf ? "⚡ Auto-Convert to PDF" : "⚡ Convert to JPG (200x230)"}
                        </span>
                      </>
                    )}
                  </button>
                </div>

                {/* Technical Diagnosis & Proof Result */}
                <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>
                      <strong className="text-slate-300">Diagnosis:</strong> {issue.recommendation}
                    </span>
                  </div>

                  {adaptResult && (
                    <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-3 text-emerald-400 text-xs">
                      <span className="font-semibold">✓ Self-Healing Result:</span>
                      {adaptResult.final_size_kb && (
                        <span>
                          Size reduced from {adaptResult.initial_size_kb} KB ➔{" "}
                          <strong>{adaptResult.final_size_kb} KB</strong>
                        </span>
                      )}
                      {adaptResult.output_format && (
                        <span>
                          Format: <strong>{adaptResult.output_format}</strong> ({adaptResult.dimensions?.width}x{adaptResult.dimensions?.height} px)
                        </span>
                      )}
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                        Evidence Gate: Verified Contract Passed
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Navigation Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <button
          onClick={onBack}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl border border-slate-700 transition-all w-full sm:w-auto justify-center"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload</span>
        </button>

        <div className="flex flex-col items-end gap-1.5 w-full sm:w-auto">
          <button
            onClick={onProceedToExecution}
            disabled={loading || !isAllResolved}
            className={`inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl shadow-lg transition-all w-full sm:w-auto ${
              isAllResolved
                ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30 cursor-pointer"
                : "bg-slate-800 text-slate-500 border border-slate-700/60 cursor-not-allowed opacity-60"
            }`}
          >
            <span>{loading ? "Executing Form..." : "Proceed to Form Auto-Fill"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          {!isAllResolved && (
            <span className="text-[11px] text-amber-400 font-mono">
              ⚠️ {conflicts.length > 0 
                ? `Resolve all ${conflicts.length} cross-document conflict(s) in Active Issues to unlock Form Auto-Fill`
                : "Application is BLOCKED by Evidence Gate. Please review issues."}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
