import React from "react";
import { ShieldCheck, Cpu, AlertTriangle, ExternalLink, Sparkles, Lock, LogOut } from "lucide-react";
import { ApplicationState } from "../types";
import { useAuth } from "../context/AuthContext";

interface NavbarProps {
  appState: ApplicationState;
  appId: string | null;
  portalSessionId: string | null;
  llmProvider: string;
  onOpenFailureBar: () => void;
  failureBarOpen: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  appState,
  appId,
  portalSessionId,
  llmProvider,
  onOpenFailureBar,
  failureBarOpen
}) => {
  const { user, isAuthenticated, openAuthModal, logout } = useAuth();
  const getStateBadgeClass = (state: ApplicationState) => {
    switch (state) {
      case "VERIFIED_SUCCESS":
        return "bg-emerald-950 text-emerald-300 border-emerald-500 shadow-emerald-900/40";
      case "VERIFICATION_FAILED":
      case "BLOCKED":
        return "bg-rose-950 text-rose-300 border-rose-500 shadow-rose-900/40";
      case "RECOVERING":
      case "REVERIFYING":
        return "bg-amber-950 text-amber-300 border-amber-500 shadow-amber-900/40";
      case "FILLING":
      case "ANALYZING":
      case "SUBMITTING":
        return "bg-blue-950 text-blue-300 border-blue-500 shadow-blue-900/40";
      default:
        return "bg-slate-900 text-slate-400 border-slate-700";
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-tight text-white">ROX</span>
              <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950/80 text-blue-400 border border-blue-800">
                A1 Evidence-Gated Agent
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Fill it. Verify it. Recover it. Prove it.</p>
          </div>
        </div>

        {/* Center: State Engine Badge */}
        <div className="flex items-center space-x-3">
          <div className={`px-3.5 py-1.5 rounded-full border text-xs font-mono font-bold flex items-center space-x-2 shadow-sm ${getStateBadgeClass(appState)}`}>
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${appState === 'VERIFIED_SUCCESS' ? 'bg-emerald-400' : 'bg-blue-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${appState === 'VERIFIED_SUCCESS' ? 'bg-emerald-500' : 'bg-blue-500'}`}></span>
            </span>
            <span>STATE: {(appState || "IDLE").replace(/_/g, " ")}</span>
          </div>

          {appId && (
            <span className="text-xs font-mono text-slate-400 hidden sm:inline-block">
              ID: <span className="text-slate-200 font-bold">{appId}</span>
            </span>
          )}
        </div>

        {/* Right Tools */}
        <div className="flex items-center space-x-3">
          {/* Failure Injection Toggle */}
          <button
            onClick={onOpenFailureBar}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 border transition ${
              failureBarOpen 
                ? "bg-amber-500/20 text-amber-300 border-amber-500/50" 
                : "bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Failure Injection</span>
          </button>

          {/* AI Engine Status Badge */}
          <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 border transition ${
            (llmProvider || "").includes("Gemini")
              ? "bg-indigo-500/15 text-indigo-300 border-indigo-500/40 shadow-sm"
              : "bg-slate-800 text-slate-300 border-slate-700"
          }`}>
            {(llmProvider || "").includes("Gemini") ? (
              <>
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                <span>Gemini 2.5 Flash Connected</span>
              </>
            ) : (
              <>
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span>Zero-Trust Hybrid Engine</span>
              </>
            )}
          </div>

          {/* Authentication & User Profile */}
          {isAuthenticated ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-md">
                {user?.email ? user.email[0].toUpperCase() : "U"}
              </div>
              <div className="hidden lg:block text-left">
                <div className="text-xs font-semibold text-slate-200 truncate max-w-[130px] font-mono">
                  {user?.email}
                </div>
                <div className="text-[10px] text-emerald-400 flex items-center space-x-1 font-medium">
                  <ShieldCheck className="w-3 h-3" />
                  <span>OTP Verified</span>
                </div>
              </div>
              <button
                onClick={logout}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-slate-700 hover:border-rose-500/40 transition text-xs"
                title="Log out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={openAuthModal}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-md shadow-indigo-500/20 border border-indigo-500/40 transition shrink-0"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Sign In (Email OTP)</span>
            </button>
          )}

          {/* Portal Link */}
          {portalSessionId && (
            <a
              href={`http://127.0.0.1:8000/portal/view/${portalSessionId}`}
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition"
              title="Open Live Simulated Portal DOM View"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </header>
  );
};
