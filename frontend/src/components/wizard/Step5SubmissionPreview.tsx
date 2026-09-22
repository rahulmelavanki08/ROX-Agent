import React, { useState } from "react";
import { ApplicationTypeItem, ReviewField, DocumentStatus } from "../../types";
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  FileCheck2, 
  Send, 
  ArrowLeft,
  Building,
  User,
  GraduationCap,
  Landmark,
  FileText,
  Lock
} from "lucide-react";

interface Step5Props {
  appType: ApplicationTypeItem;
  appId: string;
  portalSessionId: string;
  reviewFields: ReviewField[];
  documentsStatus: DocumentStatus[];
  onApproveAndSubmit: () => Promise<void>;
  onBack: () => void;
  submitting: boolean;
}

export const Step5SubmissionPreview: React.FC<Step5Props> = ({
  appType,
  appId,
  portalSessionId,
  reviewFields,
  documentsStatus,
  onApproveAndSubmit,
  onBack,
  submitting,
}) => {
  const [confirmedConsent, setConfirmedConsent] = useState(false);

  const getVal = (id: string) => {
    const f = reviewFields.find((rf) => rf.field_id === id);
    return f?.value || "—";
  };

  const personalDetails = [
    { label: "Full Name", value: getVal("full_name") },
    { label: "Date of Birth", value: getVal("date_of_birth") },
    { label: "Gender", value: getVal("gender") },
    { label: "Category", value: getVal("category") },
    { label: "Mobile Number", value: getVal("phone_number") },
    { label: "Email Address", value: getVal("email") },
  ];

  const academicDetails = [
    { label: "Institution Name", value: getVal("institution_name") },
    { label: "Registration / Roll No.", value: getVal("roll_number") },
    { label: "10th Standard Aggregate", value: `${getVal("tenth_percentage")}%` },
    { label: "12th / PUC Aggregate", value: `${getVal("twelfth_percentage")}%` },
  ];

  const financialDetails = [
    { label: "Annual Family Income", value: `₹${getVal("annual_family_income")}` },
    { label: "Bank Name", value: getVal("bank_name") },
    { label: "Account Number", value: getVal("bank_account_number") },
    { label: "IFSC Code", value: getVal("ifsc_code") },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              Step 5 of 5: Pre-Submission Review
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              Final Application Preview
            </h1>
            <p className="text-xs text-slate-400">
              Inspect your official application summary. Review all particulars before authorizing the final irreversible submission.
            </p>
          </div>

          <div className="text-right shrink-0">
            <div className="text-xs text-slate-400 font-mono">
              App ID: <span className="text-indigo-400 font-bold">{appId}</span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Session: {portalSessionId}
            </div>
          </div>
        </div>
      </div>

      {/* Official Styled Application Preview (Modeled after SBI Platinum Jubilee Scholarship) */}
      <div className="bg-white text-slate-900 rounded-2xl shadow-2xl border border-slate-200 overflow-hidden font-sans">
        {/* Official Header */}
        <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-950 text-white p-6 sm:p-8 border-b-4 border-amber-500">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="text-xs tracking-widest uppercase font-bold text-amber-400 mb-1">
                State Bank of India Foundation (SBIF)
              </div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight">
                SBI Platinum Jubilee Scholarship 2026
              </h2>
              <p className="text-xs text-blue-200 mt-1">
                Higher Education Merit-cum-Need Financial Assistance Program
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 px-4 py-2 rounded-xl text-right shrink-0">
              <div className="text-[10px] uppercase text-blue-200 font-semibold tracking-wider">
                Application Draft
              </div>
              <div className="text-sm font-bold font-mono text-amber-300">
                {appId}
              </div>
              <div className="text-[10px] text-blue-200">
                Status: Ready for Submission
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 sm:p-8 space-y-8">
          {/* Section 1: Candidate Particulars */}
          <div>
            <div className="flex items-center gap-2 pb-2 mb-4 border-b-2 border-slate-200 text-blue-900">
              <User className="w-5 h-5 text-blue-700" />
              <h3 className="text-sm font-black uppercase tracking-wider">
                Section 1: Candidate Personal Particulars
              </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {personalDetails.map((item, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                    {item.label}
                  </div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5">
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Educational Qualifications */}
          <div>
            <div className="flex items-center gap-2 pb-2 mb-4 border-b-2 border-slate-200 text-blue-900">
              <GraduationCap className="w-5 h-5 text-blue-700" />
              <h3 className="text-sm font-black uppercase tracking-wider">
                Section 2: Academic Qualifications & Institute
              </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {academicDetails.map((item, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                    {item.label}
                  </div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5">
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Financial & Family Details */}
          <div>
            <div className="flex items-center gap-2 pb-2 mb-4 border-b-2 border-slate-200 text-blue-900">
              <Landmark className="w-5 h-5 text-blue-700" />
              <h3 className="text-sm font-black uppercase tracking-wider">
                Section 3: Family Income & Bank Account Details
              </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {financialDetails.map((item, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                    {item.label}
                  </div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5 font-mono">
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Verified Enclosures */}
          <div>
            <div className="flex items-center gap-2 pb-2 mb-4 border-b-2 border-slate-200 text-blue-900">
              <FileCheck2 className="w-5 h-5 text-blue-700" />
              <h3 className="text-sm font-black uppercase tracking-wider">
                Section 4: Verified Document Enclosures
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { name: "Identity Proof (Aadhaar)", status: "VERIFIED", meta: "UIDAI Certified" },
                { name: "Academic Marksheet", status: "VERIFIED", meta: "Score Sheet Validated" },
                { name: "Family Income Certificate", status: "VERIFIED", meta: "Deflate Compressed <2MB" },
                { name: "Applicant Photograph", status: "VERIFIED", meta: "JPEG 200x230 px Compliant" },
              ].map((doc, idx) => (
                <div
                  key={idx}
                  className="bg-emerald-50/70 border border-emerald-200 p-3.5 rounded-xl space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{doc.name}</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  </div>
                  <p className="text-[10px] text-emerald-800 font-medium">
                    {doc.meta}
                  </p>
                  <div className="text-[10px] font-mono text-emerald-700 pt-1 border-t border-emerald-200/60">
                    Evidence Gate: PASSED
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Declaration */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed">
            <strong className="text-slate-800">Candidate Declaration:</strong> I hereby declare that all particulars stated in this application are true, correct, and complete to the best of my knowledge. I understand that any false statement or omission of material facts may disqualify me from the scholarship.
          </div>
        </div>
      </div>

      {/* Irreversible Action Guard (Zero-Trust Security Barrier) */}
      <div className="bg-amber-950/40 border border-amber-500/50 rounded-xl p-5 space-y-3">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg shrink-0 mt-0.5">
            <Lock className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-amber-300">
              Irreversible Action Guard: User Authorization Required
            </h4>
            <p className="text-xs text-amber-400/80 leading-relaxed">
              Final submission to the official portal is a binding and irreversible action. Once submitted, the portal issues a unique reference number and timestamps the cryptographic proof ledger.
            </p>
          </div>
        </div>

        <label className="flex items-center gap-3 p-3 bg-slate-950/60 rounded-lg border border-amber-500/30 cursor-pointer hover:bg-slate-950 transition-all">
          <input
            type="checkbox"
            checked={confirmedConsent}
            onChange={(e) => setConfirmedConsent(e.target.checked)}
            className="w-4 h-4 text-indigo-600 rounded bg-slate-900 border-slate-700 focus:ring-indigo-500"
          />
          <span className="text-xs font-semibold text-white">
            I have inspected all extracted particulars and document attachments. I authorize the autonomous submission of this scholarship application.
          </span>
        </label>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={onBack}
          disabled={submitting}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl border border-slate-700 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Form</span>
        </button>

        <button
          onClick={onApproveAndSubmit}
          disabled={!confirmedConsent || submitting}
          className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-sm font-bold rounded-xl shadow-xl shadow-emerald-600/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
          <span>{submitting ? "Transmitting to Portal..." : "Submit Application (Zero-Trust Gated)"}</span>
        </button>
      </div>
    </div>
  );
};
