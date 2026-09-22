import React from "react";
import { CheckCircle2, ChevronRight } from "lucide-react";

interface WizardStepperProps {
  currentStep: number;
  maxStepReached: number;
  onStepClick: (step: number) => void;
  canAccessStep?: (step: number) => { allowed: boolean; reason?: string };
}

const STEPS = [
  { step: 1, title: "Select Type", desc: "Choose application" },
  { step: 2, title: "Upload Documents", desc: "Checklist & upload" },
  { step: 3, title: "AI Issue Analysis", desc: "Extraction & self-healing" },
  { step: 4, title: "Form Execution", desc: "Auto-fill & evidence" },
  { step: 5, title: "Final Preview", desc: "Review & authorize" },
  { step: 6, title: "Verified Proof", desc: "Submission receipt" },
];

export const WizardStepper: React.FC<WizardStepperProps> = ({
  currentStep,
  maxStepReached,
  onStepClick,
  canAccessStep,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 shadow-lg shadow-black/20">
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        {STEPS.map((s, idx) => {
          const isCurrent = currentStep === s.step;
          const isCompleted = s.step < currentStep || (currentStep === 6 && s.step === 6);
          const access = canAccessStep ? canAccessStep(s.step) : { allowed: s.step <= maxStepReached };
          const isClickable = access.allowed;

          return (
            <button
              key={s.step}
              onClick={() => isClickable && onStepClick(s.step)}
              disabled={!isClickable}
              title={!isClickable ? (access.reason || "Complete previous steps first") : undefined}
              className={`flex items-center gap-3 p-2.5 rounded-lg text-left transition-all relative ${
                isCurrent
                  ? "bg-indigo-600/20 border border-indigo-500/50 text-white shadow-sm"
                  : isCompleted
                  ? "bg-slate-800/60 border border-emerald-500/30 text-slate-300 hover:bg-slate-800"
                  : "bg-slate-950/40 border border-slate-800/60 text-slate-500 opacity-60 cursor-not-allowed"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                  isCurrent
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/50"
                    : isCompleted
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {isCompleted && s.step < currentStep ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  s.step
                )}
              </div>

              <div className="overflow-hidden min-w-0">
                <div
                  className={`text-xs font-semibold truncate ${
                    isCurrent ? "text-indigo-300" : isCompleted ? "text-slate-200" : "text-slate-500"
                  }`}
                >
                  {s.title}
                </div>
                <div className="text-[10px] text-slate-500 truncate hidden sm:block">
                  {s.desc}
                </div>
              </div>

              {idx < STEPS.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 hidden md:block absolute -right-2 z-10" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
