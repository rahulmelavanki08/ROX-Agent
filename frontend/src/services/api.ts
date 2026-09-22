const API_BASE = "http://127.0.0.1:8000/api/v1";
const PORTAL_BASE = "http://127.0.0.1:8000/portal";

export const api = {
  async getApplicationTypes() {
    const res = await fetch(`${API_BASE}/application-types`);
    return res.json();
  },

  async getConfig() {
    const res = await fetch(`${API_BASE}/config`);
    return res.json();
  },

  async setGeminiKey(key: string) {
    const res = await fetch(`${API_BASE}/config/set-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gemini_api_key: key })
    });
    return res.json();
  },

  async initApplication(applicationType: string = "scholarship_sbi", portalUrl?: string, userGoal?: string) {
    const res = await fetch(`${API_BASE}/applications/init`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        application_type: applicationType,
        portal_url: portalUrl || "http://127.0.0.1:8000/portal",
        user_goal: userGoal || "Complete this scholarship application using my uploaded documents."
      })
    });
    return res.json();
  },

  async loadSampleDocs(appId: string) {
    const res = await fetch(`${API_BASE}/sample-docs/load?application_id=${appId}`, {
      method: "POST"
    });
    return res.json();
  },

  async getDocuments(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/documents`);
    return res.json();
  },

  async adaptFile(appId: string, fileName: string, action: "compress_pdf" | "convert_image" | "convert_to_pdf") {
    const res = await fetch(`${API_BASE}/applications/${appId}/adapt-file`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_name: fileName,
        action: action
      })
    });
    return res.json();
  },

  async autoAdaptAll(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/auto-adapt-all`, {
      method: "POST"
    });
    return res.json();
  },

  async uploadFile(appId: string, file: File, docType?: string) {
    const formData = new FormData();
    formData.append("file", file);
    if (docType) {
      formData.append("doc_type", docType);
    }
    const res = await fetch(`${API_BASE}/applications/${appId}/upload`, {
      method: "POST",
      body: formData
    });
    return res.json();
  },

  async updateField(appId: string, fieldId: string, value: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/update-field`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        field_id: fieldId,
        value: value
      })
    });
    return res.json();
  },

  async analyzeApplication(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/analyze`, {
      method: "POST"
    });
    return res.json();
  },

  async resolveConflict(appId: string, fieldId: string, chosenValue: string, source: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/resolve-conflict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        field_id: fieldId,
        chosen_value: chosenValue,
        source_reference: source
      })
    });
    return res.json();
  },

  async approvePlan(appId: string, approved: boolean, modificationRequest?: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/approve-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        approved,
        modification_request: modificationRequest || null
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to approve plan");
    }
    return data;
  },

  async executeApplication(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/execute`, {
      method: "POST"
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Execution failed");
    }
    return data;
  },

  async getReviewData(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/review-data`);
    return res.json();
  },

  async approveSubmission(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/approve-submission`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_confirmed: true })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to approve submission");
    }
    return data;
  },

  async submitApplication(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/submit`, {
      method: "POST"
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Submission failed");
    }
    return data;
  },

  async getState(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/state`);
    return res.json();
  },

  async getLedger(appId: string) {
    const res = await fetch(`${API_BASE}/applications/${appId}/ledger`);
    return res.json();
  },

  async getFailureFlags() {
    const res = await fetch(`${PORTAL_BASE}/api/failure-injection`);
    return res.json();
  },

  async updateFailureFlags(flags: any) {
    const res = await fetch(`${PORTAL_BASE}/api/failure-injection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(flags)
    });
    return res.json();
  },

  // Authentication API endpoints
  async requestOtp(email: string) {
    const res = await fetch(`${API_BASE}/auth/request-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to send OTP verification email");
    }
    return data;
  },

  async verifyOtp(email: string, otp: string) {
    const res = await fetch(`${API_BASE}/auth/verify-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Invalid or expired verification code");
    }
    return data;
  },

  async getMe(token: string) {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) return null;
    return res.json();
  },

  async logout(token: string) {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
    return res.json();
  },

  async getRecentDeliveries() {
    const res = await fetch(`${API_BASE}/auth/recent-deliveries`);
    return res.json();
  }
};
