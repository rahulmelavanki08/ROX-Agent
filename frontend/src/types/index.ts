export type ApplicationState = 
  | "NOT_STARTED"
  | "ANALYZING"
  | "AWAITING_PLAN_APPROVAL"
  | "PLANNED"
  | "BUILDING_STATE"
  | "FILLING"
  | "VERIFYING"
  | "BLOCKED"
  | "RECOVERING"
  | "REVERIFYING"
  | "READY_FOR_REVIEW"
  | "AWAITING_USER_SUBMISSION_APPROVAL"
  | "SUBMITTING"
  | "SUBMISSION_UNKNOWN"
  | "VERIFYING_SUBMISSION"
  | "VERIFIED_SUCCESS"
  | "VERIFICATION_FAILED";

export interface ConflictCandidate {
  value: string;
  source_file: string;
  source_page: number;
  evidence_text: string;
  confidence: number;
}

export interface ConflictReport {
  field_id: string;
  field_label: string;
  candidates: ConflictCandidate[];
  blocking_reason: string;
}

export interface PlanStep {
  step_number: number;
  title: string;
  description: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  requires_evidence: boolean;
  status: string;
}

export interface ApplicationPlan {
  plan_id: string;
  title: string;
  steps: PlanStep[];
  user_approved: boolean;
  modifications: string[];
}

export interface ActionContract {
  action_id: string;
  name: string;
  step_category: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  preconditions: string[];
  precondition_results?: Record<string, boolean>;
  execution_command: string;
  observation?: any;
  postconditions: string[];
  postcondition_results?: Record<string, boolean>;
  evidence?: any;
  status: "PENDING" | "IN_PROGRESS" | "VERIFIED" | "FAILED" | "RECOVERING" | "BLOCKED";
  attempt: number;
  max_attempts: number;
  error_message?: string;
  created_at?: number;
  completed_at?: number;
}

export interface LedgerEntry {
  step_id: string;
  action: string;
  actor: string;
  timestamp: number;
  formatted_time: string;
  observation?: any;
  evidence?: any;
  status: string;
  attempt: number;
  recovery_details?: any;
  entry_hash?: string;
}

export interface ApplicationMetrics {
  total_actions: number;
  verified_actions: number;
  failed_actions: number;
  recovery_count: number;
  fields_verified: string;
  documents_verified: string;
  unresolved_conflicts: number;
  submission_status: string;
}

export interface ReviewField {
  field_id: string;
  label: string;
  value: string | null;
  source_file: string | null;
  source_page: number;
  evidence_text: string | null;
  confidence: number;
  status: string;
}

export interface DocumentStatus {
  document_key: string;
  label: string;
  status: string;
  verified: boolean;
}

export interface FailureFlags {
  reject_oversized_income: boolean;
  strict_photo_requirements: boolean;
  simulate_session_expire: boolean;
  simulate_save_timeout: boolean;
  simulate_schema_change: boolean;
}

export interface RequiredDocSpec {
  key: string;
  name: string;
  description: string;
  accepted_formats: string[];
  max_size_kb: number;
  dimensions?: [number, number];
  required: boolean;
  sample_match?: string;
  known_issue?: string;
}

export interface ApplicationTypeItem {
  id: string;
  title: string;
  category: string;
  authority: string;
  deadline: string;
  description: string;
  icon: string;
  badge: string;
  portal_url: string;
  required_documents: RequiredDocSpec[];
  form_sections: { name: string; fields: string[] }[];
}

export interface FileIssue {
  file_name: string;
  file_path: string;
  file_type: "PDF" | "IMAGE" | string;
  issue_type: "OVERSIZED_FILE" | "UNSUPPORTED_FORMAT_OR_DIMENSIONS" | string;
  severity: "CRITICAL" | "WARNING" | string;
  current_size_kb?: number;
  current_size_mb?: number;
  limit_kb?: number;
  limit_mb?: number;
  current_format?: string;
  required_format?: string;
  current_dimensions?: [number, number];
  required_dimensions?: [number, number];
  message: string;
  recommendation: string;
  action_required: "compress_pdf" | "convert_image" | string;
}

export interface UploadedDocItem {
  file_name: string;
  file_path: string;
  extension: string;
  file_size_kb: number;
  file_size_mb: number;
  doc_type?: string;
  is_compressed?: boolean;
  is_adapted?: boolean;
}

export interface LLMAuditMatch {
  field: string;
  status: string;
  details?: string;
}

export interface LLMAuditDiscrepancy {
  field: string;
  status: string;
  details?: string;
}

export interface LLMAudit {
  same_person: boolean;
  confidence: number;
  summary: string;
  key_matches?: LLMAuditMatch[];
  discrepancies?: LLMAuditDiscrepancy[];
  llm_verdict?: string;
}

export interface LLMFaultReply {
  fault_title: string;
  fault_category: string;
  severity: string;
  llm_agent_reply: string;
  recovery_action?: string;
}

