import { Shield, Settings } from "lucide-react";

interface Props {
  onSettingsClick?: () => void;
  keyConfigured?: boolean;
}

export default function Header({ onSettingsClick, keyConfigured }: Props) {
  return (
    <header className="bg-gradient-to-r from-navy to-teal text-white">
      <div className="max-w-6xl mx-auto px-6 py-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-10 h-10" />
            <h1 className="text-3xl font-bold tracking-tight">ClaimClear AI</h1>
            <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-white/20 rounded-full">
              PRO
            </span>
          </div>
          <p className="text-white/80 text-lg">
            Making insurance decisions crystal clear
          </p>
        </div>
        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            className="relative mt-1 p-2 rounded-lg hover:bg-white/10 transition-colors"
            title="Settings"
          >
            <Settings className="w-6 h-6" />
            <span
              className={`absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full border-2 border-teal
                          ${keyConfigured ? "bg-emerald-400" : "bg-amber-400"}`}
            />
          </button>
        )}
      </div>
    </header>
  );
}
