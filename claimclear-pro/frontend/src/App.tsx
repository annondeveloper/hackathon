import { useState, useEffect } from "react";
import Header from "./components/Header";
import ClaimForm from "./components/ClaimForm";
import ExplanationResult from "./components/ExplanationResult";
import Footer from "./components/Footer";
import {
  explainClaim,
  getSamples,
  healthCheck,
  DEMO_RESPONSE,
  DEMO_SAMPLES,
} from "./api/client";
import type { ClaimRequest, ClaimResponse, SampleClaim } from "./types";
import { AlertTriangle } from "lucide-react";

export default function App() {
  const [samples, setSamples] = useState<SampleClaim[]>(DEMO_SAMPLES);
  const [result, setResult] = useState<ClaimResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    (async () => {
      const online = await healthCheck();
      setBackendOnline(online);
      if (online) {
        try {
          const s = await getSamples();
          setSamples(s);
        } catch {
          /* use demo samples */
        }
      }
    })();
  }, []);

  async function handleSubmit(request: ClaimRequest) {
    setLoading(true);
    setError(null);
    setResult(null);

    if (!backendOnline) {
      // Demo mode — simulate delay then show demo response
      await new Promise((r) => setTimeout(r, 1200));
      setResult(DEMO_RESPONSE);
      setLoading(false);
      return;
    }

    try {
      const response = await explainClaim(request);
      setResult(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`Failed to generate explanation: ${msg}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 space-y-8">
        {backendOnline === false && (
          <div className="flex items-center gap-2 bg-amber-50 border border-amber-200
                          text-amber-800 px-4 py-3 rounded-lg text-sm">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>
              <strong>Demo Mode</strong> — Backend not detected. Showing sample
              explanations. Start the Rust backend for live AI generation.
            </span>
          </div>
        )}

        <ClaimForm samples={samples} onSubmit={handleSubmit} loading={loading} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {result && <ExplanationResult result={result} />}
      </main>

      <Footer />
    </div>
  );
}
