import { useState, type FormEvent } from "react";
import { FileText, Sparkles, Loader2 } from "lucide-react";
import type {
  ClaimRequest,
  PolicyType,
  ClaimDecision,
  Tone,
  ReadingLevel,
  SampleClaim,
} from "../types";

interface Props {
  samples: SampleClaim[];
  onSubmit: (request: ClaimRequest) => void;
  loading: boolean;
}

const POLICY_TYPES: PolicyType[] = ["Health", "Auto", "Home", "Life", "Travel"];
const DECISIONS: ClaimDecision[] = ["Approved", "Partially Approved", "Denied", "Under Review"];
const TONES: Tone[] = ["Simple & Friendly", "Professional", "Technical"];
const READING_LEVELS: ReadingLevel[] = ["Basic", "Intermediate", "Advanced"];

export default function ClaimForm({ samples, onSubmit, loading }: Props) {
  const [claimId, setClaimId] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [policyType, setPolicyType] = useState<PolicyType>("Health");
  const [claimAmount, setClaimAmount] = useState<number>(0);
  const [decision, setDecision] = useState<ClaimDecision>("Denied");
  const [decisionReason, setDecisionReason] = useState("");
  const [policyTerms, setPolicyTerms] = useState("");
  const [tone, setTone] = useState<Tone>("Simple & Friendly");
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>("Basic");

  function loadSample(sample: SampleClaim) {
    setClaimId(sample.claim_id);
    setCustomerName(sample.customer_name);
    setPolicyType(sample.policy_type);
    setClaimAmount(sample.claim_amount);
    setDecision(sample.decision);
    setDecisionReason(sample.decision_reason);
    setPolicyTerms(sample.policy_terms);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      claim_id: claimId,
      customer_name: customerName,
      policy_type: policyType,
      claim_amount: claimAmount,
      decision,
      decision_reason: decisionReason,
      policy_terms: policyTerms,
      tone,
      reading_level: readingLevel,
    });
  }

  return (
    <div className="card animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-navy" />
          <h2 className="text-xl font-semibold text-navy">Claim Details</h2>
        </div>
        <div className="flex gap-2 flex-wrap">
          {samples.map((s) => (
            <button
              key={s.claim_id}
              type="button"
              onClick={() => loadSample(s)}
              className="text-xs px-3 py-1.5 bg-teal/10 text-teal rounded-full
                         hover:bg-teal/20 transition-colors"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-4">
            <div>
              <label className="label">Claim ID</label>
              <input className="input-field" value={claimId} onChange={(e) => setClaimId(e.target.value)} placeholder="CLM-2024-XXXXX" required />
            </div>
            <div>
              <label className="label">Customer Name</label>
              <input className="input-field" value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Full name" required />
            </div>
            <div>
              <label className="label">Policy Type</label>
              <select className="input-field" value={policyType} onChange={(e) => setPolicyType(e.target.value as PolicyType)}>
                {POLICY_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Claim Amount ($)</label>
              <input className="input-field" type="number" min={0} step={100} value={claimAmount} onChange={(e) => setClaimAmount(Number(e.target.value))} required />
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            <div>
              <label className="label">Claim Decision</label>
              <select className="input-field" value={decision} onChange={(e) => setDecision(e.target.value as ClaimDecision)}>
                {DECISIONS.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Decision Reason</label>
              <textarea className="input-field h-24 resize-none" value={decisionReason} onChange={(e) => setDecisionReason(e.target.value)} placeholder="Why was this decision made?" required />
            </div>
            <div>
              <label className="label">Policy Terms Referenced</label>
              <textarea className="input-field h-24 resize-none" value={policyTerms} onChange={(e) => setPolicyTerms(e.target.value)} placeholder="Relevant policy sections..." />
            </div>
          </div>
        </div>

        {/* Tone & Reading Level */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div>
            <label className="label">Explanation Tone</label>
            <select className="input-field" value={tone} onChange={(e) => setTone(e.target.value as Tone)}>
              {TONES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Reading Level</label>
            <select className="input-field" value={readingLevel} onChange={(e) => setReadingLevel(e.target.value as ReadingLevel)}>
              {READING_LEVELS.map((r) => <option key={r}>{r}</option>)}
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary w-full mt-8 flex items-center justify-center gap-2" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate Explanation
            </>
          )}
        </button>
      </form>
    </div>
  );
}
