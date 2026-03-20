import { useState } from "react";
import { Copy, Download, Clock, Brain, BookOpen, ChevronDown, ChevronUp, CheckCircle } from "lucide-react";
import type { ClaimResponse } from "../types";

interface Props {
  result: ClaimResponse;
}

export default function ExplanationResult({ result }: Props) {
  const [expandedTerms, setExpandedTerms] = useState<Set<number>>(new Set());
  const [copied, setCopied] = useState(false);

  function toggleTerm(idx: number) {
    setExpandedTerms((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  async function copyToClipboard() {
    await navigator.clipboard.writeText(result.explanation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadText() {
    const blob = new Blob([result.explanation], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `claim_explanation_${result.request_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const scoreColor =
    result.comprehension_score >= 8 ? "text-green-500" :
    result.comprehension_score >= 6 ? "text-yellow-500" : "text-red-500";

  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (result.comprehension_score / 10) * circumference;

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Explanation Card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-navy flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Generated Explanation
          </h2>
          <div className="flex gap-2">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-200
                         rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Copy className="w-4 h-4" />
              {copied ? "Copied!" : "Copy"}
            </button>
            <button
              onClick={downloadText}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-200
                         rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-teal-50 border-l-4 border-teal
                        rounded-r-lg p-6 prose prose-sm max-w-none whitespace-pre-wrap">
          {result.explanation}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Comprehension Score Gauge */}
        <div className="card flex flex-col items-center">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="40" fill="none"
                stroke="currentColor"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className={`${scoreColor} transition-all duration-1000`}
              />
            </svg>
            <span className={`absolute inset-0 flex items-center justify-center text-2xl font-bold ${scoreColor}`}>
              {result.comprehension_score}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-2 flex items-center gap-1">
            <Brain className="w-4 h-4" /> Comprehension Score
          </p>
        </div>

        {/* Time Saved */}
        <div className="card flex flex-col items-center justify-center">
          <Clock className="w-8 h-8 text-teal mb-2" />
          <p className="text-3xl font-bold text-navy">~12 min</p>
          <p className="text-sm text-gray-500">Estimated Time Saved</p>
        </div>

        {/* Processing Time */}
        <div className="card flex flex-col items-center justify-center">
          <BookOpen className="w-8 h-8 text-teal mb-2" />
          <p className="text-3xl font-bold text-navy">{result.processing_time_ms}ms</p>
          <p className="text-sm text-gray-500">Processing Time</p>
        </div>
      </div>

      {/* Glossary Accordion */}
      {result.glossary.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Key Terms Glossary
          </h3>
          <div className="space-y-2">
            {result.glossary.map((item, idx) => (
              <div key={idx} className="border border-gray-100 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleTerm(idx)}
                  className="w-full flex items-center justify-between px-4 py-3
                             bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                >
                  <span className="font-medium text-navy">{item.term}</span>
                  {expandedTerms.has(idx) ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </button>
                {expandedTerms.has(idx) && (
                  <div className="px-4 py-3 text-sm text-gray-600 bg-white animate-fade-in">
                    {item.definition}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
