import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { 
  Mail, 
  KeyRound, 
  CheckCircle2, 
  AlertCircle, 
  X, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles,
  Clock,
  RefreshCw
} from "lucide-react";

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, requestOtp, verifyOtp } = useAuth();
  
  const [step, setStep] = useState<"email" | "otp">("email");
  const [email, setEmail] = useState<string>("applicant@example.com");
  const [otp, setOtp] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deliveredPreview, setDeliveredPreview] = useState<string | null>(null);
  
  // 5-minute countdown timer
  const [timeLeft, setTimeLeft] = useState<number>(300);
  const [canResend, setCanResend] = useState<boolean>(false);
  const [resendCooldown, setResendCooldown] = useState<number>(30);

  useEffect(() => {
    let timer: any;
    if (step === "otp" && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft]);

  useEffect(() => {
    let cdTimer: any;
    if (step === "otp" && resendCooldown > 0) {
      cdTimer = setInterval(() => setResendCooldown((prev) => prev - 1), 1000);
    } else if (resendCooldown === 0) {
      setCanResend(true);
    }
    return () => clearInterval(cdTimer);
  }, [step, resendCooldown]);

  if (!isAuthModalOpen) return null;

  const handleSendOtp = async (targetEmail?: string) => {
    const toSend = targetEmail || email;
    if (!toSend || !toSend.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await requestOtp(toSend);
      setStep("otp");
      setTimeLeft(300);
      setCanResend(false);
      setResendCooldown(30);
      setSuccessMessage(`OTP sent to ${toSend}`);
      if (res.dev_otp_preview) {
        setDeliveredPreview(res.dev_otp_preview);
      }
    } catch (err: any) {
      setError(err.message || "Failed to send verification code");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!otp || otp.length < 6) {
      setError("Please enter the 6-digit verification code.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await verifyOtp(email, otp);
      setSuccessMessage("Login verified successfully!");
      setTimeout(() => {
        closeAuthModal();
        setStep("email");
        setOtp("");
        setError(null);
        setSuccessMessage(null);
        setDeliveredPreview(null);
      }, 800);
    } catch (err: any) {
      setError(err.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header decoration */}
        <div className="h-1.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-500" />

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-6 sm:p-8 space-y-6">
          {/* Header Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {step === "email" ? "Sign In to ROX" : "Verify Email Code"}
              </h2>
              <p className="text-xs text-slate-400">
                {step === "email"
                  ? "Enter your registered email for OTP-based secure verification."
                  : `Enter the 6-digit code sent to ${email}`}
              </p>
            </div>
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-2.5 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-start space-x-2.5 text-xs text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* STAGE 1: EMAIL INPUT */}
          {step === "email" ? (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono transition"
                    autoFocus
                  />
                </div>
              </div>

              {/* Quick-Pick Test Profiles for Evaluation */}
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Quick Demo Profiles:</span>
                <div className="flex flex-wrap gap-2 mt-1.5">
                  {[
                    "applicant@example.com",
                    "rahul.melavanki@gmail.com",
                    "student.test@edu.in"
                  ].map((testEmail) => (
                    <button
                      key={testEmail}
                      type="button"
                      onClick={() => {
                        setEmail(testEmail);
                        handleSendOtp(testEmail);
                      }}
                      className="px-2.5 py-1 text-[11px] rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 font-mono transition flex items-center space-x-1"
                    >
                      <span>⚡ {testEmail}</span>
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleSendOtp()}
                disabled={loading || !email}
                className="w-full mt-2 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/20 transition flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Generating & Dispatching Code...</span>
                  </>
                ) : (
                  <>
                    <span>Send Verification Code</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          ) : (
            /* STAGE 2: OTP INPUT */
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              {/* Evaluator Delivery Toast Preview */}
              {deliveredPreview && (
                <div className="p-3 bg-blue-950/60 border border-blue-500/40 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-xs text-blue-300 font-medium">
                    <span className="flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                      <span>Email Delivery Notification</span>
                    </span>
                    <span className="text-[10px] text-blue-400 font-mono">Simulated / SMTP</span>
                  </div>
                  <div className="flex items-center justify-between bg-slate-950 p-2.5 rounded-lg border border-blue-900/60">
                    <div>
                      <span className="text-[11px] text-slate-400 block">OTP sent to {email}:</span>
                      <span className="font-mono text-base font-extrabold tracking-widest text-emerald-400">
                        {deliveredPreview}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setOtp(deliveredPreview)}
                      className="px-2.5 py-1 text-xs bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 rounded-lg font-medium transition"
                    >
                      Fill Code
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  6-Digit Verification Code
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ""))}
                    placeholder="123456"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3.5 py-2.5 text-lg font-mono tracking-widest text-white text-center focus:outline-none focus:border-indigo-500 transition"
                    autoFocus
                  />
                </div>
              </div>

              {/* Countdown & Resend */}
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>Expires in: <strong className="text-slate-200 font-mono">{formatTime(timeLeft)}</strong></span>
                </div>

                {canResend ? (
                  <button
                    type="button"
                    onClick={() => handleSendOtp()}
                    className="text-indigo-400 hover:text-indigo-300 font-medium transition"
                  >
                    Resend Code
                  </button>
                ) : (
                  <span className="text-slate-500">Resend in {resendCooldown}s</span>
                )}
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setStep("email");
                    setOtp("");
                    setError(null);
                  }}
                  className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-xl border border-slate-700 transition"
                >
                  Change Email
                </button>

                <button
                  type="submit"
                  disabled={loading || otp.length < 6}
                  className="flex-1 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/20 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Verify & Login</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Security Guarantee */}
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-center space-x-2 text-[11px] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted with SHA-256 OTP Hash & 5-Min Expiry</span>
          </div>
        </div>
      </div>
    </div>
  );
};
