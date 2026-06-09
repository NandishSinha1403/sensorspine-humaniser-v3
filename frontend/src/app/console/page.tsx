"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  History, 
  Sparkles, 
  Copy, 
  Terminal,
  ChevronDown,
  Settings,
  UserCircle,
  Home as HomeIcon
} from "lucide-react";
import Link from "next/link";

export default function ConsolePage() {
  // --- STATE ---
  const [text, setText] = useState("");
  const [intensity, setIntensity] = useState(0.7);
  const [backendUrl, setBackendUrl] = useState("https://broodless-suzan-nonprohibitively.ngrok-free.dev");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // --- LOGIC ---
  const handleHumanize = async () => {
    if (!backendUrl) {
      setError("Please enter the Backend URL (from Colab/ngrok)");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setStatusMessage("Authenticating with SOTA Gateway...");

    try {
      const tokenResponse = await fetch(`${backendUrl}/token`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/x-www-form-urlencoded",
          "ngrok-skip-browser-warning": "true"
        },
        body: new URLSearchParams(),
      });
      
      if (!tokenResponse.ok) throw new Error("Authentication failed");
      const { access_token } = await tokenResponse.json();

      setStatusMessage("Submitting text for semantic evasion...");
      const submitResponse = await fetch(`${backendUrl}/humanize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${access_token}`,
          "ngrok-skip-browser-warning": "true"
        },
        body: JSON.stringify({ text, intensity }),
      });

      if (!submitResponse.ok) {
        const errData = await submitResponse.json();
        throw new Error(errData.detail || "Failed to submit task");
      }
      
      const { task_id } = await submitResponse.json();

      let completed = false;
      let attempts = 0;
      const maxAttempts = 40;

      while (!completed && attempts < maxAttempts) {
        attempts++;
        setStatusMessage(`AI Neutralization in progress... (Step ${attempts})`);
        await new Promise(resolve => setTimeout(resolve, 3000));

        const statusResponse = await fetch(`${backendUrl}/status/${task_id}`, {
          headers: { 
            "Authorization": `Bearer ${access_token}`,
            "ngrok-skip-browser-warning": "true"
          }
        });

        if (!statusResponse.ok) throw new Error("Status check failed");
        const statusData = await statusResponse.json();

        if (statusData.status === "completed") {
          setResult(statusData);
          completed = true;
        } else if (statusData.status === "failed" || statusData.status === "error") {
          throw new Error(statusData.error || statusData.message || "Task failed in Colab");
        }
      }

      if (!completed) throw new Error("Task timed out. Check your Colab worker logs.");

    } catch (err: any) {
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
      setStatusMessage("");
    }
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  return (
    <div className="min-h-screen bg-black text-on-surface overflow-x-hidden selection:bg-blue-500/30">
      {/* Immersive Background Image (GIF) */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none flex items-center justify-center bg-black">
        <img 
          src="/orb.gif"
          alt="Ambient Background"
          className="w-[120vw] h-[120vw] max-w-none md:w-[80vw] md:h-[80vw] object-cover opacity-80"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/90 via-black/30 to-black/90" />
      </div>

      {/* Ambient Background Glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[600px] h-[600px] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none z-0 animate-drift" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[800px] h-[800px] bg-emerald-600/5 blur-[150px] rounded-full pointer-events-none z-0 animate-drift" style={{ animationDelay: "-5s" }} />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-6 md:px-16 py-4 bg-black/40 backdrop-blur-2xl border-b border-white/10">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-playfair text-2xl md:text-3xl font-bold tracking-tighter text-white hover:opacity-80 transition-opacity">
            ScholarAI
          </Link>
          <div className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-xs font-semibold uppercase tracking-widest text-slate-400 hover:text-white transition-colors flex items-center gap-2">
              <HomeIcon size={14} /> Home
            </Link>
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 border-b border-blue-400 pb-1">Console</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="hidden md:block text-slate-400 hover:text-white transition-colors"><Settings size={20} /></button>
          <button className="hidden md:block text-slate-400 hover:text-white transition-colors"><UserCircle size={20} /></button>
          <Link href="/" className="px-5 py-2 rounded-full border border-white/20 text-white text-xs font-bold uppercase tracking-widest hover:bg-white/5 transition-all">
            Exit Console
          </Link>
        </div>
      </nav>

      {/* Main Console Canvas */}
      <main className="relative z-10 pt-32 px-6 max-w-7xl mx-auto pb-12">
        <header className="mb-12 flex flex-col md:flex-row justify-between items-end gap-6">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-2"
          >
            <h2 className="font-playfair text-4xl md:text-5xl font-bold text-white tracking-tight">Semantic Evasion Console</h2>
            <p className="text-slate-400 max-w-2xl text-sm">Calibrate structural anomalies and execute deep textual restructuring to bypass detection heuristics.</p>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2 bg-slate-900/50 px-4 py-2 rounded-full border border-white/5"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
            <span className="font-mono text-[10px] text-emerald-400 uppercase tracking-widest">System Online</span>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Main Content Column (Left - 8 cols) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-8 flex flex-col gap-6"
          >
            {/* Input Canvas */}
            <div className="glass-card rounded-2xl p-6 flex flex-col h-[350px]">
              <div className="flex justify-between items-center mb-4">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Source Material</label>
                <span className="font-mono text-[10px] text-slate-500">{text.length} / 5000 chars</span>
              </div>
              <textarea 
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste AI-generated text here for analysis..."
                className="w-full flex-grow bg-black/40 border border-white/5 rounded-xl p-4 font-sans text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors resize-none"
              />
            </div>

            {/* Results Grid (Below Input) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[400px]">
              {/* Original Baseline */}
              <div className="glass-card rounded-2xl p-6 flex flex-col overflow-hidden h-full">
                <div className="flex items-center gap-2 text-slate-500 mb-4 shrink-0">
                  <History size={16} />
                  <span className="text-[10px] font-bold uppercase tracking-widest">Original Baseline</span>
                </div>
                <div className="flex-grow bg-black/40 rounded-xl p-4 text-sm text-slate-400 leading-relaxed overflow-y-auto font-sans min-h-0">
                  {text || "Awaiting input source..."}
                </div>
              </div>

              {/* Reconstructed Output */}
              <div className="glass-card rounded-2xl p-6 flex flex-col relative overflow-hidden border-emerald-500/40 shadow-[0_0_50px_rgba(16,185,129,0.15)] h-full ring-1 ring-emerald-400/20">
                <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 blur-[60px] pointer-events-none animate-pulse-glow" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 blur-[60px] pointer-events-none animate-pulse-glow" style={{ animationDelay: "-2s" }} />
                
                <div className="flex items-center justify-between mb-4 shrink-0 relative z-10">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <Sparkles size={18} className="animate-pulse" />
                    <span className="text-[12px] font-bold uppercase tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-blue-400">Reconstructed Output</span>
                  </div>
                  {result && (
                    <button 
                      onClick={() => copyToClipboard(result.humanized)}
                      className="text-emerald-500 hover:text-emerald-300 transition-colors bg-emerald-500/10 p-2 rounded-lg hover:bg-emerald-500/20"
                    >
                      <Copy size={16} />
                    </button>
                  )}
                </div>
                
                <div className="flex-grow bg-[#050a08]/80 backdrop-blur-md border border-emerald-500/20 rounded-xl p-5 text-sm text-slate-100 leading-relaxed overflow-y-auto font-sans font-medium min-h-0 relative z-10 shadow-inner">
                  {result ? result.humanized : "Awaiting execution payload..."}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Side Control Panel (Right - 4 cols) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-4 flex flex-col gap-6 sticky top-24"
          >
            {/* Controls */}
            <div className="glass-card rounded-2xl p-6 space-y-8">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Evasion Intensity</label>
                  <span className="font-mono text-xs text-blue-400 font-bold">{intensity} μ</span>
                </div>
                <input 
                  type="range" 
                  min="0.1" 
                  max="1.0" 
                  step="0.1" 
                  value={intensity}
                  onChange={(e) => setIntensity(parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-full appearance-none cursor-pointer accent-blue-500"
                />
                <div className="flex justify-between mt-2 font-mono text-[8px] text-slate-600">
                  <span>0.1 (SURFACE)</span>
                  <span>1.0 (DEEP ANOMALY)</span>
                </div>
              </div>

              <div className="border-t border-white/5 pt-6">
                <button 
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="w-full flex justify-between items-center text-slate-400 hover:text-white transition-colors"
                >
                  <span className="text-[10px] font-bold uppercase tracking-widest">Advanced Protocols</span>
                  <ChevronDown size={14} className={`transform transition-transform ${showAdvanced ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence>
                  {showAdvanced && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-4 space-y-4">
                        <div className="space-y-2">
                          <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Backend Endpoint</label>
                          <input 
                            type="text"
                            value={backendUrl}
                            onChange={(e) => setBackendUrl(e.target.value)}
                            className="w-full bg-black/40 border border-white/5 rounded-lg p-3 text-xs text-slate-300 font-mono focus:border-blue-500/50 outline-none"
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Execute Button */}
            <button 
              onClick={handleHumanize}
              disabled={loading || !text}
              className={`w-full py-5 rounded-xl font-bold uppercase tracking-[0.2em] text-xs transition-all flex flex-col items-center justify-center gap-1 group relative overflow-hidden
                ${loading ? "bg-blue-600/50 text-white/50 cursor-wait" : "bg-blue-600 text-white hover:bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.2)] hover:shadow-[0_0_30px_rgba(59,130,246,0.4)]"}
              `}
            >
              {loading ? (
                <>
                  <Sparkles size={20} className="animate-spin mb-1" />
                  <span>Neutralizing...</span>
                  <span className="text-[8px] font-normal tracking-widest opacity-60">{statusMessage}</span>
                </>
              ) : (
                <>
                  <span className="relative z-10 flex items-center gap-2">
                    Execute Semantic Evasion <Sparkles size={16} />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-transparent opacity-0 group-hover:opacity-20 transition-opacity" />
                </>
              )}
            </button>
            {error && <p className="text-red-400 text-center text-[10px] font-bold uppercase tracking-widest">{error}</p>}

            {/* Confidence Score */}
            <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-6">Evasion Confidence</span>
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                  <motion.circle 
                    cx="50" cy="50" r="45" fill="none" 
                    stroke="#10b981" strokeWidth="8"
                    strokeDasharray="283"
                    initial={{ strokeDashoffset: 283 }}
                    animate={{ strokeDashoffset: result ? 283 - (283 * result.confidence_score) : 283 }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]"
                  />
                </svg>
                <span className="text-3xl font-bold text-emerald-400">
                  {result ? Math.round(result.confidence_score * 100) : "0"}<span className="text-xs">%</span>
                </span>
              </div>
            </div>

            {/* Logs */}
            <div className="glass-card rounded-2xl flex-grow overflow-hidden flex flex-col min-h-[200px]">
              <div className="px-4 py-3 border-b border-white/5 bg-black/40 flex justify-between items-center">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em]">AMR Structural Surgery Log</span>
                <Terminal size={14} className="text-slate-500" />
              </div>
              <div className="p-4 bg-black/60 border-l-2 border-blue-500/50 flex-grow font-mono text-[10px] text-slate-500 overflow-y-auto h-[140px] space-y-1">
                <div>&gt; Initializing heuristic bypass sequence...</div>
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ repeat: Infinity, duration: 1, repeatType: "reverse" }}
                  >
                    &gt; {statusMessage}
                  </motion.div>
                )}
                {result && (
                  <>
                    <div className="text-emerald-500">&gt; Semantic restructuring complete.</div>
                    <div className="text-blue-400">&gt; AMR Path: {result.amr_intermediate?.substring(0, 100)}...</div>
                    <div className="text-indigo-400">&gt; Confidence: {result.confidence_score}</div>
                    {result.diagnostics && (
                      <>
                        <div className="text-slate-400">&gt; AI Prob (post-NLP): {result.diagnostics.ai_probability}</div>
                        {result.diagnostics.pre_nlp_ai_probability != null && (
                          <div className="text-slate-500">&gt; AI Prob (post-LLM): {result.diagnostics.pre_nlp_ai_probability}</div>
                        )}
                        <div className="text-slate-400">&gt; Burstiness: {result.diagnostics.burstiness}</div>
                      </>
                    )}
                  </>
                )}
                {!loading && !result && <div>&gt; Awaiting execution payload...</div>}
              </div>
            </div>

          </motion.div>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-white/5 py-12 px-6 md:px-16 mt-12 bg-black/40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="space-y-2 text-center md:text-left">
            <h3 className="font-playfair text-xl font-bold text-white tracking-tighter">ScholarAI Console</h3>
            <p className="text-[9px] text-slate-600 uppercase tracking-[0.3em]">
              © 2026 Sensorspine Pvt. Ltd. | Dev: Nandish Sinha
            </p>
          </div>
          <div className="flex gap-6">
            <Link href="/" className="text-[10px] text-slate-500 hover:text-blue-400 transition-colors uppercase tracking-widest">Back to Landing</Link>
            <a href="#" className="text-[10px] text-slate-500 hover:text-blue-400 transition-colors uppercase tracking-widest">Support</a>
            <a href="#" className="text-[10px] text-slate-500 hover:text-blue-400 transition-colors uppercase tracking-widest">API Docs</a>
          </div>
        </div>
      </footer>
    </div>
  );
}