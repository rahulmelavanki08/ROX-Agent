import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { MetricCards } from "./components/MetricCards";
import { FailureInjectionBar } from "./components/FailureInjectionBar";
import { ActionContractDrawer } from "./components/ActionContractDrawer";
import { ProofLedgerModal } from "./components/ProofLedgerModal";
import { WizardStepper } from "./components/wizard/WizardStepper";
import { Step1SelectApplication } from "./components/wizard/Step1SelectApplication";
import { Step2UploadDocuments } from "./components/wizard/Step2UploadDocuments";
import { Step3IssueAnalysis } from "./components/wizard/Step3IssueAnalysis";
import { Step4FormExecution } from "./components/wizard/Step4FormExecution";
import { Step5SubmissionPreview } from "./components/wizard/Step5SubmissionPreview";
import { Step6VerifiedResult } from "./components/wizard/Step6VerifiedResult";
import { api } from "./services/api";
import { 
  ApplicationState, 
  ApplicationMetrics, 
  ConflictReport, 
  ActionContract, 
  LedgerEntry, 
  ReviewField, 
  DocumentStatus, 
  FailureFlags,
  ApplicationTypeItem,
  FileIssue,
  UploadedDocItem,
  LLMAudit,
  LLMFaultReply
} from "./types";
import { RefreshCw, Terminal, Layers } from "lucide-react";
import { AuthProvider } from "./context/AuthContext";
import { AuthModal } from "./components/AuthModal";

function AppContent() {
  // Wizard Navigation
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [maxStepReached, setMaxStepReached] = useState<number>(1);

  // Application Catalog
  const [applicationTypes, setApplicationTypes] = useState<ApplicationTypeItem[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState<string>("scholarship_sbi");

  // App Session
  const [appId, setAppId] = useState<string | null>(null);
  const [portalSessionId, setPortalSessionId] = useState<string | null>(null);
  const [appState, setAppState] = useState<ApplicationState>("NOT_STARTED");
  const [metrics, setMetrics] = useState<ApplicationMetrics | null>(null);
  const [llmProvider, setLlmProvider] = useState<string>("MockLLMProvider");
  const [failureBarOpen, setFailureBarOpen] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(Date.now());

  // Documents & Issues
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocItem[]>([]);
  const [fileIssues, setFileIssues] = useState<FileIssue[]>([]);
  const [conflicts, setConflicts] = useState<ConflictReport[]>([]);
  const [reviewFields, setReviewFields] = useState<ReviewField[]>([]);
  const [documentsStatus, setDocumentsStatus] = useState<DocumentStatus[]>([]);
  const [actionContracts, setActionContracts] = useState<ActionContract[]>([]);
  const [portalState, setPortalState] = useState<any>(null);
  const [submissionResult, setSubmissionResult] = useState<any>(null);
  const [llmAudit, setLlmAudit] = useState<LLMAudit | null>(null);
  const [llmFaultReplies, setLlmFaultReplies] = useState<LLMFaultReply[]>([]);

  // Modals & Drawers
  const [showLedgerModal, setShowLedgerModal] = useState<boolean>(false);
  const [showContractDrawer, setShowContractDrawer] = useState<boolean>(false);
  const [selectedContract, setSelectedContract] = useState<ActionContract | null>(null);
  const [ledgerEntries, setLedgerEntries] = useState<LedgerEntry[]>([]);

  // Failure Injection
  const [failureFlags, setFailureFlags] = useState<FailureFlags>({
    reject_oversized_income: true,
    strict_photo_requirements: true,
    simulate_session_expire: false,
    simulate_save_timeout: false,
    simulate_schema_change: false
  });

  // Loading indicator
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);

  // Load Catalog on Mount
  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const res = await api.getApplicationTypes();
        if (res && res.types) {
          setApplicationTypes(res.types);
        }
      } catch (err) {
        console.error("Failed to load application types:", err);
      }
    };
    loadCatalog();
  }, []);

  // Poll state
  const fetchState = async () => {
    try {
      const cfg = await api.getConfig();
      if (cfg && cfg.llm_provider) {
        setLlmProvider(cfg.llm_provider);
      }

      if (appId) {
        const stateRes = await api.getState(appId);
        if (stateRes && stateRes.detail && typeof stateRes.detail === "string" && stateRes.detail.toLowerCase().includes("not found")) {
          setAppId(null);
          setPortalSessionId(null);
          setAppState("NOT_STARTED");
          return;
        }
        if (stateRes && stateRes.state) setAppState(stateRes.state);
        if (stateRes && stateRes.metrics) setMetrics(stateRes.metrics);
        if (stateRes && stateRes.portal_session_id) setPortalSessionId(stateRes.portal_session_id);
        if (stateRes && stateRes.portal_state) setPortalState(stateRes.portal_state);
        if (stateRes && stateRes.conflicts) setConflicts(stateRes.conflicts);
        if (stateRes && stateRes.file_issues) setFileIssues(stateRes.file_issues);
        if (stateRes && stateRes.llm_audit) setLlmAudit(stateRes.llm_audit);
        if (stateRes && stateRes.llm_fault_replies) setLlmFaultReplies(stateRes.llm_fault_replies);

        const ledg = await api.getLedger(appId);
        if (ledg && ledg.entries) setLedgerEntries(ledg.entries);

        const docsRes = await api.getDocuments(appId);
        if (docsRes && docsRes.documents) setUploadedDocs(docsRes.documents);
      }
    } catch (e) {
      console.warn("Fetch state error:", e);
    }
  };

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 3000);
    return () => clearInterval(interval);
  }, [appId]);

  // WebSocket Live Updates with auto-reconnect
  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: any = null;

    const connect = () => {
      try {
        socket = new WebSocket("ws://127.0.0.1:8000/ws/live");
        socket.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.event_type === "state_changed" && msg.to_state) {
              setAppState(msg.to_state);
            }
            setRefreshTrigger(Date.now());
            if (appId) {
              fetchState();
            }
          } catch (e) {}
        };
        socket.onerror = () => {
          // Handled silently; auto-reconnect will re-establish
        };
        socket.onclose = () => {
          reconnectTimer = setTimeout(connect, 4000);
        };
      } catch (e) {}
    };

    connect();
    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [appId]);

  // Step 1 -> Step 2: Initialize Application
  const handleProceedFromStep1 = async () => {
    setLoadingAction("Creating application context...");
    try {
      const res = await api.initApplication(selectedTypeId);
      setAppId(res.application_id);
      setPortalSessionId(res.portal_session_id);
      setAppState(res.state);
      await fetchState();
      setCurrentStep(2);
      setMaxStepReached((prev) => Math.max(prev, 2));
    } finally {
      setLoadingAction(null);
    }
  };

  // Step 2: Upload File
  const handleUploadFile = async (file: File, docType?: string) => {
    if (!appId) return;
    setLoadingAction(`Uploading ${file.name}...`);
    try {
      await api.uploadFile(appId, file, docType);
      const docsRes = await api.getDocuments(appId);
      setUploadedDocs(docsRes.documents || []);
      await fetchState();
    } finally {
      setLoadingAction(null);
    }
  };

  // Step 2: 1-Click Load Demo Documents
  const handleLoadSampleDocs = async () => {
    let currentAppId = appId;
    if (!currentAppId) {
      const res = await api.initApplication(selectedTypeId);
      currentAppId = res.application_id;
      setAppId(res.application_id);
      setPortalSessionId(res.portal_session_id);
      setAppState(res.state);
    }

    setLoadingAction("Loading sample demo documents...");
    try {
      await api.loadSampleDocs(currentAppId!);
      const docsRes = await api.getDocuments(currentAppId!);
      setUploadedDocs(docsRes.documents || []);
      await fetchState();
    } finally {
      setLoadingAction(null);
    }
  };

  // Strict Stage Validation Gate
  const canAccessStep = (targetStep: number): { allowed: boolean; reason?: string } => {
    if (targetStep <= 1) return { allowed: true };
    if (targetStep === 2) {
      return appId ? { allowed: true } : { allowed: false, reason: "Please select an application scheme in Step 1 first." };
    }
    if (targetStep === 3) {
      if (!appId) return { allowed: false, reason: "Please select an application scheme first." };
      if (uploadedDocs.length === 0) {
        return { allowed: false, reason: "Please upload at least one document in Step 2 first (or click 'Auto-Load Demo Documents')." };
      }
      return { allowed: true };
    }
    if (targetStep === 4) {
      if (!appId) return { allowed: false, reason: "Please select an application scheme first." };
      if (reviewFields.length === 0) return { allowed: false, reason: "Please run AI Extraction & Analysis in Step 3 first." };
      if (conflicts.length > 0 || appState === "BLOCKED") {
        return { allowed: false, reason: `Cannot access Step 4: Application has ${conflicts.length || 'active'} unresolved cross-document identity conflict(s). Please resolve them in Step 3 first.` };
      }
      return { allowed: true };
    }
    if (targetStep === 5) {
      if (!appId) return { allowed: false, reason: "Please select an application scheme first." };
      if (actionContracts.length === 0 || !["READY_FOR_REVIEW", "AWAITING_USER_SUBMISSION_APPROVAL", "SUBMITTING", "VERIFIED_SUCCESS"].includes(appState)) {
        return { allowed: false, reason: "Please execute form auto-fill in Step 4 first." };
      }
      return { allowed: true };
    }
    if (targetStep === 6) {
      if (appState !== "VERIFIED_SUCCESS") {
        return { allowed: false, reason: "Please authorize and submit the application in Step 5 first." };
      }
      return { allowed: true };
    }
    return { allowed: false, reason: "Invalid step." };
  };

  const handleStepClick = (step: number) => {
    const check = canAccessStep(step);
    if (!check.allowed) {
      alert(check.reason || "Please complete the previous steps before advancing.");
      return;
    }
    setCurrentStep(step);
  };

  // Step 2 -> Step 3: Analyze
  const handleProceedToAnalyze = async () => {
    if (!appId) {
      alert("Please select an application scheme first.");
      return;
    }
    if (uploadedDocs.length === 0) {
      alert("Please upload at least one document or use 'Auto-Load Demo Documents' to extract and analyze.");
      return;
    }

    setLoadingAction("Extracting document entities & analyzing portal constraints with AI...");
    try {
      const res = await api.analyzeApplication(appId);
      if (res) {
        if (res.state) setAppState(res.state);
        setConflicts(res.mapping?.conflicts || []);
        setFileIssues(res.file_issues || []);
        if (res.llm_audit) setLlmAudit(res.llm_audit);
        if (res.llm_fault_replies) setLlmFaultReplies(res.llm_fault_replies);

        // Zero-Touch Automation: Automatically convert images to PDF and compress oversized files
        if (res.file_issues && res.file_issues.length > 0) {
          setLoadingAction("Zero-Touch Self-Healing: Auto-converting documents to PDF and compressing sizes...");
          try {
            const adaptRes = await api.autoAdaptAll(appId);
            if (adaptRes && adaptRes.status === "SUCCESS") {
              setFileIssues([]);
            }
          } catch (adaptErr) {
            console.error("Auto-adapt all during analysis transition failed:", adaptErr);
          }
        }
      }

      // Load review fields
      try {
        const rev = await api.getReviewData(appId);
        if (rev) {
          setReviewFields(rev.review_fields || []);
          setDocumentsStatus(rev.documents_status || []);
        }
      } catch (revErr) {
        console.warn("Failed to fetch review data:", revErr);
      }

      await fetchState();
      setCurrentStep(3);
      setMaxStepReached((prev) => Math.max(prev, 3));
    } catch (err: any) {
      console.error("AI Analysis error:", err);
      // Fallback transition so user is never stuck
      try {
        const rev = await api.getReviewData(appId);
        if (rev) {
          setReviewFields(rev.review_fields || []);
          setDocumentsStatus(rev.documents_status || []);
        }
      } catch (e) {}
      await fetchState();
      setCurrentStep(3);
      setMaxStepReached((prev) => Math.max(prev, 3));
    } finally {
      setLoadingAction(null);
    }
  };

  // Step 3: Resolve Conflict
  const handleResolveConflict = async (fieldId: string, value: string, source: string) => {
    if (!appId) return;
    setLoadingAction("Applying verified conflict resolution...");
    try {
      await api.resolveConflict(appId, fieldId, value, source);
      setConflicts((prev) => prev.filter((c) => c.field_id !== fieldId));
      const rev = await api.getReviewData(appId);
      if (rev && rev.review_fields) setReviewFields(rev.review_fields);
      await fetchState();
    } finally {
      setLoadingAction(null);
    }
  };

  // Step 3: Inline Field Update / Add Override
  const handleUpdateField = async (fieldId: string, value: string) => {
    if (!appId) return;
    setLoadingAction(`Updating field "${fieldId}"...`);
    try {
      await api.updateField(appId, fieldId, value);
      const rev = await api.getReviewData(appId);
      setReviewFields(rev.review_fields || []);
      await fetchState();
    } finally {
      setLoadingAction(null);
    }
  };

  // Step 3: Adapt File (Compress or Convert)
  const handleAdaptFile = async (fileName: string, action: "compress_pdf" | "convert_image" | "convert_to_pdf") => {
    if (!appId) return;
    const res = await api.adaptFile(appId, fileName, action);
    // Remove from file issues
    setFileIssues((prev) => prev.filter((fi) => fi.file_name !== fileName));
    const docsRes = await api.getDocuments(appId);
    setUploadedDocs(docsRes.documents || []);
    await fetchState();
    return res;
  };

  // Step 3: Zero-Touch Auto Adapt All
  const handleAutoAdaptAll = async () => {
    if (!appId) return;
    try {
      const res = await api.autoAdaptAll(appId);
      setFileIssues([]);
      const docsRes = await api.getDocuments(appId);
      setUploadedDocs(docsRes.documents || []);
      await fetchState();
      return res;
    } catch (e) {
      console.error("Auto adapt all failed:", e);
    }
  };

  // Step 3 -> Step 4: Run Execution
  const handleProceedToExecution = async () => {
    if (!appId) return;
    if (appState === "BLOCKED" || conflicts.length > 0) {
      alert(`⚠️ Cannot advance to Step 4: Application is BLOCKED by the Evidence Gate due to ${conflicts.length} unresolved identity mismatch conflict(s). Please choose which record is correct in Active Issues before proceeding.`);
      return;
    }
    setCurrentStep(4);
    setMaxStepReached((prev) => Math.max(prev, 4));
    handleTriggerExecution();
  };

  // Step 4: Execute Action Contracts
  const handleTriggerExecution = async () => {
    if (!appId) return;
    if (appState === "BLOCKED" || conflicts.length > 0) {
      alert(`⚠️ Cannot execute form filling: Application is BLOCKED due to unresolved identity conflicts. Please resolve them in Step 3 first.`);
      setCurrentStep(3);
      return;
    }
    setExecuting(true);
    setLoadingAction("Executing action contracts with deterministic evidence gating...");
    try {
      try {
        await api.approvePlan(appId, true);
      } catch (e: any) {
        console.warn("Plan approval note:", e?.message);
      }

      const res = await api.executeApplication(appId);
      if (res && res.state) {
        setAppState(res.state);
      }
      if (res && res.actions_executed) {
        setActionContracts(res.actions_executed);
      }
      const rev = await api.getReviewData(appId);
      if (rev && rev.review_fields) {
        setReviewFields(rev.review_fields);
      }
      if (rev && rev.documents_status) {
        setDocumentsStatus(rev.documents_status);
      }
      await fetchState();
    } catch (err: any) {
      console.error("Execution error:", err);
      alert(`Execution halted: ${err?.message || "An error occurred during execution."}`);
      await fetchState();
    } finally {
      setExecuting(false);
      setLoadingAction(null);
    }
  };

  // Step 4 -> Step 5: Pre-submission Preview
  const handleProceedToPreview = async () => {
    if (!appId) return;
    const rev = await api.getReviewData(appId);
    setReviewFields(rev.review_fields || []);
    setDocumentsStatus(rev.documents_status || []);
    setCurrentStep(5);
    setMaxStepReached((prev) => Math.max(prev, 5));
  };

  // Step 5 -> Step 6: Submit Application
  const handleApproveAndSubmit = async () => {
    if (!appId) return;
    setLoadingAction("Authorizing irreversible action & submitting to portal...");
    try {
      await api.approveSubmission(appId);
      const res = await api.submitApplication(appId);
      setSubmissionResult(res.submission_details || res);
      setAppState(res.state);
      await fetchState();
      setCurrentStep(6);
      setMaxStepReached(6);
    } finally {
      setLoadingAction(null);
    }
  };

  // Reset to Step 1
  const handleReset = () => {
    setAppId(null);
    setPortalSessionId(null);
    setAppState("NOT_STARTED");
    setUploadedDocs([]);
    setFileIssues([]);
    setConflicts([]);
    setReviewFields([]);
    setActionContracts([]);
    setSubmissionResult(null);
    setCurrentStep(1);
    setMaxStepReached(1);
  };

  const selectedApp = applicationTypes.find((t) => t.id === selectedTypeId) || applicationTypes[0] || {
    id: "scholarship_sbi",
    title: "SBI Platinum Jubilee Scholarship 2026",
    category: "Scholarship",
    authority: "State Bank of India Foundation (SBIF)",
    deadline: "31-Mar-2026",
    description: "Financial assistance program for meritorious students.",
    icon: "GraduationCap",
    badge: "Track A1 Benchmark",
    portal_url: "http://localhost:8000/portal",
    required_documents: [],
    form_sections: []
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Navbar */}
      <Navbar
        appState={appState}
        appId={appId}
        portalSessionId={portalSessionId}
        llmProvider={llmProvider}
        onOpenFailureBar={() => setFailureBarOpen(!failureBarOpen)}
        failureBarOpen={failureBarOpen}
      />

      {/* Failure Injection Deck */}
      <FailureInjectionBar
        flags={failureFlags}
        onToggleFlag={async (key) => {
          const next = { ...failureFlags, [key]: !failureFlags[key] };
          setFailureFlags(next);
          await api.updateFailureFlags(next);
        }}
        isOpen={failureBarOpen}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 flex flex-col">
        {/* Metric Cards */}
        {metrics && (
          <div className="mb-6">
            <MetricCards metrics={metrics} />
          </div>
        )}

        {/* Wizard Stepper Header */}
        <WizardStepper
          currentStep={currentStep}
          maxStepReached={maxStepReached}
          onStepClick={handleStepClick}
          canAccessStep={canAccessStep}
        />

        {/* Global Loading Pill */}
        {loadingAction && (
          <div className="mb-6 p-3.5 rounded-xl bg-indigo-950/60 border border-indigo-800 text-indigo-200 text-xs font-mono flex items-center space-x-3 animate-pulse shadow-md">
            <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
            <span>{loadingAction}</span>
          </div>
        )}

        {/* Active Step Content */}
        <div className="flex-1">
          {currentStep === 1 && (
            <Step1SelectApplication
              types={applicationTypes}
              selectedTypeId={selectedTypeId}
              onSelectType={(id) => setSelectedTypeId(id)}
              onProceed={handleProceedFromStep1}
              loading={Boolean(loadingAction)}
            />
          )}

          {currentStep === 2 && (
            <Step2UploadDocuments
              appType={selectedApp}
              appId={appId || "DEMO"}
              uploadedDocs={uploadedDocs}
              onUploadFile={handleUploadFile}
              onLoadSampleDocs={handleLoadSampleDocs}
              onProceedToAnalyze={handleProceedToAnalyze}
              onBack={() => setCurrentStep(1)}
              loading={Boolean(loadingAction)}
            />
          )}

          {currentStep === 3 && (
            <Step3IssueAnalysis
              appState={appState}
              conflicts={conflicts}
              fileIssues={fileIssues}
              reviewFields={reviewFields}
              llmAudit={llmAudit}
              llmFaultReplies={llmFaultReplies}
              llmProvider={llmProvider}
              onResolveConflict={handleResolveConflict}
              onAdaptFile={handleAdaptFile}
              onAutoAdaptAll={handleAutoAdaptAll}
              onUpdateField={handleUpdateField}
              onProceedToExecution={handleProceedToExecution}
              onBack={() => setCurrentStep(2)}
              loading={Boolean(loadingAction)}
            />
          )}

          {currentStep === 4 && (
            <Step4FormExecution
              appId={appId || "DEMO"}
              contracts={actionContracts}
              reviewFields={reviewFields}
              portalState={portalState}
              onProceedToPreview={handleProceedToPreview}
              onBack={() => setCurrentStep(3)}
              loading={Boolean(loadingAction)}
              executing={executing}
              onTriggerExecution={handleTriggerExecution}
            />
          )}

          {currentStep === 5 && (
            <Step5SubmissionPreview
              appType={selectedApp}
              appId={appId || "DEMO"}
              portalSessionId={portalSessionId || "SESSION_001"}
              reviewFields={reviewFields}
              documentsStatus={documentsStatus}
              onApproveAndSubmit={handleApproveAndSubmit}
              onBack={() => setCurrentStep(4)}
              submitting={Boolean(loadingAction)}
            />
          )}

          {currentStep === 6 && (
            <Step6VerifiedResult
              appId={appId || "DEMO"}
              submissionDetails={submissionResult}
              onOpenLedger={() => setShowLedgerModal(true)}
              onOpenAudit={() => setShowContractDrawer(true)}
              onReset={handleReset}
            />
          )}
        </div>

        {/* Global Quick Utility Footer Bar */}
        <div className="mt-8 pt-4 border-t border-slate-900 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2 font-mono">
            <span>ROX Engine v1.0</span>
            <span>•</span>
            <span>Zero-Trust Architecture</span>
            <span>•</span>
            <span>Track A1 Benchmark</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowLedgerModal(true)}
              className="hover:text-slate-300 transition flex items-center gap-1.5 font-mono"
            >
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              <span>Cryptographic Proof Ledger ({ledgerEntries.length})</span>
            </button>
            <span>•</span>
            <button
              onClick={() => setShowContractDrawer(true)}
              className="hover:text-slate-300 transition flex items-center gap-1.5 font-mono"
            >
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <span>Contracts Inspector</span>
            </button>
          </div>
        </div>
      </main>

      {/* Modals & Drawers */}
      <ProofLedgerModal
        entries={ledgerEntries}
        appId={appId || "DEMO"}
        onClose={() => setShowLedgerModal(false)}
        isOpen={showLedgerModal}
      />

      <ActionContractDrawer
        contract={selectedContract}
        onClose={() => setShowContractDrawer(false)}
        isOpen={showContractDrawer}
      />

      {/* Secure OTP Email Verification Modal */}
      <AuthModal />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
