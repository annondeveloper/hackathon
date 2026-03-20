import { Shield } from "lucide-react";

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-navy to-teal text-white">
      <div className="max-w-6xl mx-auto px-6 py-8">
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
    </header>
  );
}
