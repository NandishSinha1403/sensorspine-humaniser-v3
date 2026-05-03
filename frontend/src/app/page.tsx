"use client";

import { useState } from "react";

export default function Home() {
  const [text, setText] = useState("");
  const [intensity, setIntensity] = useState(1.0);
  const [backendUrl, setBackendUrl] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleHumanize = async () => {
    if (!backendUrl) {
      setError("Please enter the Backend URL (from Colab/ngrok)");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${backendUrl}/humanize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, intensity }),
      });

      if (!response.ok) throw new Error("Backend error");

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="text-center space-y-2">
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            ScholarAI v3 SOTA
          </h1>
          <p className="text-slate-400">Deep Semantic Evasion Humanizer</p>
        </header>

        <section className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 space-y-2">
              <label className="block text-sm font-medium text-slate-300">Backend URL</label>
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                placeholder="https://xxxx-xx-xx-xx.ngrok-free.app"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="block text-sm font-medium text-slate-300">Intensity: {intensity}</label>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.1"
                value={intensity}
                onChange={(e) => setIntensity(parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500 mt-4"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">Input AI Text</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-4 text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              placeholder="Paste AI-generated text here..."
            />
          </div>

          <button
            onClick={handleHumanize}
            disabled={loading || !text}
            className="w-full bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 disabled:opacity-50 text-white font-bold py-3 rounded-lg transition-all shadow-lg"
          >
            {loading ? "Humanizing... (This may take 30-60s)" : "Execute Semantic Evasion"}
          </button>
          
          {error && <p className="text-red-400 text-center text-sm">{error}</p>}
        </section>

        {result && (
          <section className="grid md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Original (AI DNA)</h3>
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{result.original}</p>
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-emerald-500/30">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">Humanized (SOTA)</h3>
                <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold">
                  {Math.round(result.confidence_score * 100)}% Human Confidence
                </span>
              </div>
              <p className="text-slate-100 leading-relaxed whitespace-pre-wrap font-medium">{result.humanized}</p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
