export interface ClaimRequest {
  claim_id: string;
  customer_name: string;
  policy_type: PolicyType;
  claim_amount: number;
  decision: ClaimDecision;
  decision_reason: string;
  policy_terms: string;
  tone: Tone;
  reading_level: ReadingLevel;
}

export type PolicyType = "Health" | "Auto" | "Home" | "Life" | "Travel";
export type ClaimDecision = "Approved" | "Partially Approved" | "Denied" | "Under Review";
export type Tone = "Simple & Friendly" | "Professional" | "Technical";
export type ReadingLevel = "Basic" | "Intermediate" | "Advanced";

export interface GlossaryTerm {
  term: string;
  definition: string;
}

export interface ClaimResponse {
  explanation: string;
  glossary: GlossaryTerm[];
  comprehension_score: number;
  processing_time_ms: number;
  request_id: string;
}

export interface ConfigStatus {
  configured: boolean;
  masked_key: string;
}

export interface SampleClaim {
  label: string;
  claim_id: string;
  customer_name: string;
  policy_type: PolicyType;
  claim_amount: number;
  decision: ClaimDecision;
  decision_reason: string;
  policy_terms: string;
}
