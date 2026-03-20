import { useState } from "react";
import { X, Eye, EyeOff, Key, Check, Trash2, ShieldCheck, AlertCircle } from "lucide-react";
import type { ConfigStatus } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  configStatus: ConfigStatus | null;
  onSave: (key: string) => Promise<void>;
  onRemove: () => Promise<void>;
}

export default function SettingsModal({ open, onClose, configStatus, onSave, onRemove }: Props) {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!open) return null;

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setError("Please enter an API key");
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await onSave(apiKey.trim());
      setApiKey("");
      setShowKey(false);
      setSuccess("API key saved securely");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save API key";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    setError(null);
    setSuccess(null);
    try {
      await onRemove();
      setSuccess("API key removed");
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError("Failed to remove API key");
    } finally {
      setRemoving(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 animate-scale-in overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-navy to-teal px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Key className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Current status */}
          <div className="flex items-start gap-3 p-4 rounded-lg bg-slate-50 border border-slate-200">
            {configStatus?.configured ? (
              <>
                <ShieldCheck className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-slate-700">API Key Configured</p>
                  <p className="text-xs text-slate-500 mt-0.5 font-mono">
                    {configStatus.masked_key}
                  </p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-slate-700">No API Key Set</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Enter your OpenAI API key below to enable live AI explanations.
                  </p>
                </div>
              </>
            )}
          </div>

          {/* API Key input */}
          <div>
            <label
              htmlFor="api-key-input"
              className="block text-sm font-medium text-slate-700 mb-1.5"
            >
              {configStatus?.configured ? "Update API Key" : "OpenAI API Key"}
            </label>
            <div className="relative">
              <input
                id="api-key-input"
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                placeholder="sk-..."
                autoComplete="off"
                spellCheck={false}
                className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-lg
                           text-sm font-mono placeholder:text-slate-400
                           focus:outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal
                           transition-shadow"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400
                           hover:text-slate-600 transition-colors"
                title={showKey ? "Hide" : "Show"}
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1.5">
              Your key is stored securely in server memory only — never written to disk or sent to third parties.
            </p>
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-lg text-sm">
              <Check className="w-4 h-4 flex-shrink-0" />
              {success}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2">
            {configStatus?.configured ? (
              <button
                onClick={handleRemove}
                disabled={removing}
                className="flex items-center gap-1.5 text-sm text-red-600 hover:text-red-700
                           disabled:opacity-50 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                {removing ? "Removing..." : "Remove Key"}
              </button>
            ) : (
              <div />
            )}
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !apiKey.trim()}
                className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-navy to-teal
                           text-white text-sm font-medium rounded-lg shadow-md
                           hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all"
              >
                {saving ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Save Key
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
