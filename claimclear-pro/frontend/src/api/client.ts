import axios from "axios";
import type { ClaimRequest, ClaimResponse, ConfigStatus, SampleClaim } from "../types";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export async function explainClaim(request: ClaimRequest): Promise<ClaimResponse> {
  const { data } = await api.post<ClaimResponse>("/explain", request);
  return data;
}

export async function getSamples(): Promise<SampleClaim[]> {
  const { data } = await api.get<SampleClaim[]>("/samples");
  return data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    await api.get("/health");
    return true;
  } catch {
    return false;
  }
}

export async function getConfigStatus(): Promise<ConfigStatus> {
  const { data } = await api.get<ConfigStatus>("/config/status");
  return data;
}

export async function setApiKey(openai_api_key: string): Promise<ConfigStatus> {
  const { data } = await api.post<ConfigStatus>("/config", { openai_api_key });
  return data;
}

export async function removeApiKey(): Promise<ConfigStatus> {
  const { data } = await api.delete<ConfigStatus>("/config");
  return data;
}

// Fallback demo data when backend is unavailable
export const DEMO_RESPONSE: ClaimResponse = {
  explanation: `Hi Sarah,

Thank you for filing your health insurance claim (CLM-2024-78432). We understand that dealing with medical bills can be stressful, so we want to clearly explain the outcome of your claim.

**What happened:** Your claim for $3,200.00 for services received at Riverside Medical Center was **denied**.

**Why this decision was made:** Your policy (Section 4.2 — Network Provider Requirements) requires that non-emergency medical services be provided by doctors and facilities within our approved network. Riverside Medical Center is not currently part of our provider network, which means the services you received there are not covered under your plan.

**What this means for you:** Because the care was received outside of the network, your plan does not cover these costs. However, this does not mean you are out of options.

**Your next steps:**
1. **Appeal the decision** — If you believe the services were medically necessary or that no in-network provider was available, you can file an appeal within 60 days.
2. **Check for exceptions** — Contact our team at 1-800-555-0199 to ask about a network gap exception.
3. **Find in-network providers** — Visit our online directory to find covered providers near you for future visits.

We are here to help you through this process. Please do not hesitate to reach out with any questions.`,
  glossary: [
    { term: "Provider Network", definition: "A group of doctors and hospitals that have agreed to provide services at pre-negotiated rates with your insurance company." },
    { term: "Out-of-Network", definition: "Healthcare providers that do not have a contract with your insurance plan, meaning services may not be covered." },
    { term: "Appeal", definition: "A formal request to have your insurance company review and reconsider a claim decision." },
    { term: "Network Gap Exception", definition: "A special approval allowing you to see an out-of-network provider at in-network rates." },
    { term: "Medically Necessary", definition: "Services required to diagnose or treat a medical condition that meet accepted standards of medical practice." },
  ],
  comprehension_score: 8.5,
  processing_time_ms: 1250,
  request_id: "demo-001",
};

export const DEMO_SAMPLES: SampleClaim[] = [
  {
    label: "Denied Health Claim — Out-of-Network",
    claim_id: "CLM-2024-78432",
    customer_name: "Sarah Johnson",
    policy_type: "Health",
    claim_amount: 3200,
    decision: "Denied",
    decision_reason: "Services were provided by an out-of-network provider (Riverside Medical Center). Policy Section 4.2 requires use of in-network providers for non-emergency services.",
    policy_terms: "Section 4.2 — Network Provider Requirements; Section 7.1 — Out-of-Network Exclusions",
  },
  {
    label: "Partially Approved Auto Claim",
    claim_id: "CLM-2024-91205",
    customer_name: "Michael Chen",
    policy_type: "Auto",
    claim_amount: 8500,
    decision: "Partially Approved",
    decision_reason: "Collision damage approved ($6,200). Aftermarket modifications ($2,300) excluded per policy terms. Deductible of $500 applies.",
    policy_terms: "Section 3.1 — Collision Coverage; Section 5.4 — Aftermarket Parts Exclusion; Schedule A — Deductible",
  },
  {
    label: "Approved Home Claim — Water Damage",
    claim_id: "CLM-2024-56789",
    customer_name: "Emily Rodriguez",
    policy_type: "Home",
    claim_amount: 15000,
    decision: "Approved",
    decision_reason: "Sudden pipe burst causing water damage to first floor. Covered peril under standard homeowners policy. Restoration costs within policy limits.",
    policy_terms: "Section 2.1 — Covered Perils (Water Damage); Section 6.3 — Dwelling Coverage Limits",
  },
];
