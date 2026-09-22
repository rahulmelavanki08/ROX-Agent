import React, { useState } from "react";
import { X, Cpu, Key, Check, ShieldCheck } from "lucide-react";
import { api } from "../services/api";

interface GeminiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentProvider: string;
  onKeyUpdated: () => void;
}

export const GeminiKeyModal: React.FC<GeminiKeyModalProps> = ({
  isOpen,
  onClose,
  currentProvider,
  onKeyUpdated
}) => {
  if (!isOpen) return null;

  const [key, setKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSave = async () => {
    if (!key.trim()) return;
    setLoading(true);
    try {
      const res = await api.setGeminiKey(key.trim());
      setMsg("Gemini API key saved! Active provider: " + res.active_provider);
      onKeyUpdated();
      setTimeout(() => {
        setMsg("");
        onClose();
      }, 1500);
    } catch (e: any) {
      setMsg("Failed to update key: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <Cpu className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">Google Gemini AI Engine</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="my-4 text-xs text-slate-300 space-y-2">
          <p>
            Current Active Cognitive Engine:{" "}
            <span className="font-mono font-bold text-blue-400">{currentProvider}</span>
          </p>
          <p className="text-slate-400 text-[11px]">
            Enter your Google Gemini API key to activate live semantic reasoning for portal analysis, document parsing, and failure recovery.
          </p>
          <div className="mt-3">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Gemini API Key:
            </label>
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>

          {msg && (
            <div className="p-2.5 rounded bg-blue-950/80 border border-blue-800 text-blue-300 text-xs font-mono mt-2">
              {msg}
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading || !key.trim()}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white disabled:opacity-50 transition"
          >
            {loading ? "Connecting..." : "Activate Gemini AI"}
          </button>
        </div>
      </div>
    </div>
  );
};
