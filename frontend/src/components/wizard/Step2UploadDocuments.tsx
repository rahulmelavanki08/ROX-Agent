import React, { useState, useRef } from "react";
import { ApplicationTypeItem, UploadedDocItem } from "../../types";
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  ArrowRight, 
  ArrowLeft, 
  FileCheck, 
  ShieldAlert
} from "lucide-react";

interface Step2Props {
  appType: ApplicationTypeItem;
  appId: string;
  uploadedDocs: UploadedDocItem[];
  onUploadFile: (file: File, docType?: string) => Promise<void>;
  onLoadSampleDocs: () => Promise<void>;
  onProceedToAnalyze: () => void;
  onBack: () => void;
  loading: boolean;
}

export const Step2UploadDocuments: React.FC<Step2Props> = ({
  appType,
  appId: _appId,
  uploadedDocs,
  onUploadFile,
  onLoadSampleDocs,
  onProceedToAnalyze,
  onBack,
  loading,
}) => {
  const [dragOverKey, setDragOverKey] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeUploadDocKey, setActiveUploadDocKey] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const targetDocType = activeUploadDocKey || undefined;
      await onUploadFile(file, targetDocType);
      e.target.value = "";
      setActiveUploadDocKey(null);
    }
  };

  const triggerUploadFor = (docKey: string) => {
    setActiveUploadDocKey(docKey);
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleDrop = async (e: React.DragEvent, docKey: string) => {
    e.preventDefault();
    setDragOverKey(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await onUploadFile(e.dataTransfer.files[0], docKey);
    }
  };

  // Match uploaded files to required document specs
  // 1. Explicit doc_type takes top precedence
  // 2. Fallback to filename substring
  const getUploadedForSpec = (specKey: string) => {
    const byDocType = uploadedDocs.find((d) => d.doc_type === specKey);
    if (byDocType) return byDocType;
    const rawKey = specKey.replace("doc_", "").toLowerCase();
    return uploadedDocs.find((d) => d.file_name.toLowerCase().includes(rawKey));
  };

  // List of missing mandatory documents
  const missingMandatoryDocs = appType.required_documents.filter((spec) => {
    if (!spec.required) return false;
    return !getUploadedForSpec(spec.key);
  });

  const allRequiredPresent = missingMandatoryDocs.length === 0;

  return (
    <div className="space-y-6">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".pdf,.png,.jpg,.jpeg,.docx"
      />

      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-1">
              Step 2 of 5: Document Upload Center
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              Upload Required Enclosures
            </h1>
            <p className="text-xs text-slate-400">
              Selected: <span className="text-slate-200 font-medium">{appType.title}</span> • Target Portal: <span className="text-slate-300 font-mono text-[11px]">{appType.portal_url}</span>
            </p>
          </div>

          {/* 1-Click Demo Button */}
          <button
            onClick={onLoadSampleDocs}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-amber-500/20 transition-all shrink-0"
          >
            <Sparkles className="w-4 h-4" />
            <span>⚡ Auto-Load Demo Documents</span>
          </button>
        </div>
      </div>

      {/* Strict Step-Completion Guard Banner */}
      {!allRequiredPresent ? (
        <div className="bg-amber-950/40 border border-amber-500/40 rounded-xl p-4 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-2 flex-1">
            <div className="text-sm font-bold text-amber-300">
              Step Incomplete: {missingMandatoryDocs.length} Mandatory Document{missingMandatoryDocs.length > 1 ? "s" : ""} Missing
            </div>
            <p className="text-xs text-amber-400/90 leading-relaxed">
              In accordance with zero-trust application gating, you cannot proceed to AI Extraction until all required enclosures are uploaded. You may upload your own files with any filename (e.g. <span className="font-mono text-amber-200">my_scan_01.pdf</span>) using the upload buttons below, or use the 1-Click Demo loader above.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-amber-400 font-semibold">Missing:</span>
              {missingMandatoryDocs.map((doc) => (
                <span
                  key={doc.key}
                  className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-200 border border-amber-500/30 text-xs font-medium"
                >
                  {doc.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <div className="text-sm font-bold text-emerald-300">
                All Mandatory Enclosures Uploaded!
              </div>
              <p className="text-xs text-emerald-400/80">
                All {appType.required_documents.length} required document slots are fulfilled. You can now proceed to AI Extraction & Constraint Analysis.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold px-2.5 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg">
            GATED: UNLOCKED
          </span>
        </div>
      )}

      {/* Checklist of Required Documents */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>Enclosures Checklist</span>
              <span className="text-[10px] text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded normal-case font-normal">
                Any custom filename supported
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Attach files to each required slot. Files will be tagged, checked for constraints, and semantically parsed for application particulars.
            </p>
          </div>
          <div className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 text-slate-300">
            {uploadedDocs.length} Uploaded
          </div>
        </div>

        <div className="space-y-3">
          {appType.required_documents.map((spec) => {
            const uploaded = getUploadedForSpec(spec.key);
            const isOversized = uploaded && uploaded.file_size_kb > spec.max_size_kb;
            const isFormatMismatch = uploaded && spec.dimensions && uploaded.extension.toLowerCase() !== ".jpg" && uploaded.extension.toLowerCase() !== ".jpeg";
            const isDragOver = dragOverKey === spec.key;

            return (
              <div
                key={spec.key}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOverKey(spec.key);
                }}
                onDragLeave={() => setDragOverKey(null)}
                onDrop={(e) => handleDrop(e, spec.key)}
                className={`p-4 rounded-xl border transition-all ${
                  isDragOver
                    ? "border-indigo-500 bg-indigo-950/30"
                    : uploaded
                    ? "border-slate-800 bg-slate-950/60"
                    : "border-slate-800/80 bg-slate-950/30 hover:border-slate-700"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div
                      className={`p-2.5 rounded-lg shrink-0 mt-0.5 ${
                        uploaded
                          ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {uploaded ? <CheckCircle2 className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-semibold text-white truncate">
                          {spec.name}
                        </span>
                        {spec.required ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                            Required
                          </span>
                        ) : (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                            Optional
                          </span>
                        )}
                        <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                          slot: {spec.key}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mb-1">
                        {spec.description}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 font-mono">
                        <span>Formats: {spec.accepted_formats.join(", ")}</span>
                        <span>• Max: {spec.max_size_kb >= 1024 ? `${spec.max_size_kb / 1024} MB` : `${spec.max_size_kb} KB`}</span>
                        {spec.dimensions && <span>• Dims: {spec.dimensions[0]}x{spec.dimensions[1]} px</span>}
                      </div>
                    </div>
                  </div>

                  {/* Upload State & Actions */}
                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                    {uploaded ? (
                      <div className="text-right">
                        <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                          <FileCheck className="w-3.5 h-3.5" />
                          <span className="truncate max-w-[180px] font-mono">{uploaded.file_name}</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {uploaded.file_size_mb >= 1 ? `${uploaded.file_size_mb} MB` : `${uploaded.file_size_kb} KB`}
                        </div>

                        {/* Edge Case Warning Indicators */}
                        {isOversized && (
                          <div className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 mt-1">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Oversized ({uploaded.file_size_mb} MB &gt; 2 MB)</span>
                          </div>
                        )}
                        {isFormatMismatch && (
                          <div className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 mt-1">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Format: {uploaded.extension.toUpperCase()} (JPG needed)</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-slate-500 italic">Not uploaded</span>
                    )}

                    <button
                      onClick={() => triggerUploadFor(spec.key)}
                      disabled={loading}
                      className={`px-3.5 py-1.5 text-xs font-medium rounded-lg border transition-all flex items-center gap-1.5 ${
                        uploaded
                          ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700"
                          : "bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border-indigo-500/30"
                      }`}
                    >
                      <UploadCloud className="w-3.5 h-3.5" />
                      <span>{uploaded ? "Replace File" : "Upload File"}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Additional / Custom Supporting Documents Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              <span>Additional Supporting Documents</span>
              <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded normal-case font-normal">
                Optional
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Upload any extra documents (Transfer Certificate, Caste/Income Slip, Bonafide, Ration Card, etc.). Gemini 3.6 Flash will extract all credentials and entities.
            </p>
          </div>

          <button
            onClick={() => triggerUploadFor("doc_additional")}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-xs font-semibold rounded-xl transition-all shrink-0"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Supporting Document</span>
          </button>
        </div>

        {/* Display list of uploaded custom files if any */}
        {uploadedDocs.filter(d => !appType.required_documents.some(spec => {
          const match = getUploadedForSpec(spec.key);
          return match && match.file_name === d.file_name;
        })).length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {uploadedDocs.filter(d => !appType.required_documents.some(spec => {
              const match = getUploadedForSpec(spec.key);
              return match && match.file_name === d.file_name;
            })).map((doc) => (
              <div
                key={doc.file_name}
                className="bg-slate-950 border border-slate-800 rounded-lg p-3 flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-2.5 overflow-hidden">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="truncate">
                    <div className="text-xs font-medium text-slate-200 truncate font-mono">
                      {doc.file_name}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {doc.file_size_mb >= 1 ? `${doc.file_size_mb} MB` : `${doc.file_size_kb} KB`} • {doc.extension.toUpperCase().replace(".", "")}
                    </div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                  Ready for AI
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div 
            onClick={() => triggerUploadFor("doc_additional")}
            className="border-2 border-dashed border-slate-800 hover:border-slate-700 rounded-xl p-5 text-center cursor-pointer transition-colors"
          >
            <UploadCloud className="w-6 h-6 text-slate-500 mx-auto mb-1.5" />
            <p className="text-xs text-slate-400">
              Drag & drop any additional documents here, or click to browse
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Supports .pdf, .jpg, .png, .docx
            </p>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <button
          onClick={onBack}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl border border-slate-700 transition-all w-full sm:w-auto justify-center"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Schemes</span>
        </button>

        <div className="flex flex-col items-end gap-1.5 w-full sm:w-auto">
          <button
            onClick={onProceedToAnalyze}
            disabled={loading || uploadedDocs.length === 0}
            className={`inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl shadow-lg transition-all w-full sm:w-auto ${
              uploadedDocs.length > 0
                ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30 cursor-pointer"
                : "bg-slate-800 text-slate-500 border border-slate-700/60 cursor-not-allowed opacity-60"
            }`}
          >
            <span>{loading ? "Extracting & Analyzing with AI..." : "Extract & Analyze with AI"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          {uploadedDocs.length === 0 ? (
            <span className="text-[11px] text-amber-400/90 font-mono">
              ⚠️ Upload at least 1 document or click "Auto-Load Demo Documents" to proceed
            </span>
          ) : !allRequiredPresent ? (
            <span className="text-[11px] text-slate-400 font-mono">
              ℹ️ Proceeding with {uploadedDocs.length} uploaded document(s) ({missingMandatoryDocs.length} slot(s) unfilled)
            </span>
          ) : (
            <span className="text-[11px] text-emerald-400 font-mono">
              ✓ All {appType.required_documents.length} mandatory documents satisfied
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
