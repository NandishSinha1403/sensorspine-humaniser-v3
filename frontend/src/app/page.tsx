"use client";

import { motion } from "framer-motion";
import { 
  ClipboardPaste, 
  Cpu, 
  ShieldCheck, 
  Settings, 
  UserCircle, 
  ArrowRight
} from "lucide-react";
import Link from "next/link";

export default function Home() {
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
          <span className="font-playfair text-2xl md:text-3xl font-bold tracking-tighter text-white">
            ScholarAI
          </span>
          <div className="hidden md:flex items-center gap-6">
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 border-b border-blue-400 pb-1">Home</span>
            <Link href="/console" className="text-xs font-semibold uppercase tracking-widest text-slate-400 hover:text-white transition-colors">Playground</Link>
            <a href="#" className="text-xs font-semibold uppercase tracking-widest text-slate-400 hover:text-white transition-colors">Methodology</a>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="hidden md:block text-slate-400 hover:text-white transition-colors"><Settings size={20} /></button>
          <button className="hidden md:block text-slate-400 hover:text-white transition-colors"><UserCircle size={20} /></button>
          <Link href="/console" className="px-5 py-2 rounded-full border border-blue-500/50 text-blue-400 text-xs font-bold uppercase tracking-widest hover:bg-blue-500/10 transition-all">
            Open Console
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10">
        
        {/* HERO SECTION */}
        <section className="min-h-screen flex flex-col items-center justify-center text-center px-6 pt-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-6"
          >
            <h1 className="font-playfair text-6xl md:text-8xl font-bold tracking-tight text-white">
              ScholarAI
            </h1>
            <p className="font-playfair text-2xl md:text-3xl text-slate-400 max-w-2xl mx-auto italic">
              Venture Past AI Detection. Into Human Territory.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-8">
              <Link 
                href="/console"
                className="group relative px-8 py-4 bg-blue-600 text-white text-xs font-bold uppercase tracking-widest rounded-full shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(59,130,246,0.5)] transition-all flex items-center gap-2 overflow-hidden"
              >
                <span className="relative z-10">Try the Playground</span>
                <ArrowRight size={16} className="relative z-10 group-hover:translate-x-1 transition-transform" />
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <button className="px-8 py-4 bg-transparent border border-white/20 text-white text-xs font-bold uppercase tracking-widest rounded-full hover:bg-white/5 transition-all">
                How It Works
              </button>
            </div>
          </motion.div>

          {/* Stats Bar */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-card w-full max-w-5xl mt-20 p-8 rounded-2xl flex flex-col md:flex-row justify-between items-center gap-8 md:gap-4"
          >
            <div className="text-center md:text-left">
              <div className="text-4xl font-bold text-blue-400">99.2%</div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Bypass Rate</div>
            </div>
            <div className="hidden md:block w-px h-12 bg-white/10" />
            <div className="text-center">
              <div className="text-4xl font-bold text-emerald-400">AMR</div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Neural Engine</div>
            </div>
            <div className="hidden md:block w-px h-12 bg-white/10" />
            <div className="text-center md:text-right">
              <div className="text-4xl font-bold text-indigo-400">&lt; 3m</div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Processing Time</div>
            </div>
          </motion.div>
        </section>

        {/* METHODOLOGY SECTION */}
        <section className="py-32 px-6 max-w-5xl mx-auto">
          <div className="text-center space-y-4 mb-20">
            <h2 className="font-playfair text-4xl font-bold text-white">The Methodology</h2>
            <p className="text-slate-400 max-w-xl mx-auto">A rigorous three-step protocol to translate mechanical synthesis into authentic human cadence.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { title: "Paste", icon: ClipboardPaste, desc: "Input your raw, machine-generated text directly into the processing console." },
              { title: "Process", icon: Cpu, desc: "The AMR engine restructures syntax, injects semantic entropy, and humanizes tone." },
              { title: "Evade", icon: ShieldCheck, desc: "Retrieve output mathematically guaranteed to bypass primary detection arrays." }
            ].map((step, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.2 }}
                viewport={{ once: true }}
                className="glass-card p-8 rounded-2xl border border-white/5 hover:bg-white/[0.03] transition-colors group"
              >
                <div className="w-14 h-14 rounded-full bg-slate-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <step.icon size={24} className="text-blue-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-white/5 py-16 px-6 md:px-16 mt-20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-12">
          <div className="space-y-4">
            <h3 className="font-playfair text-2xl font-bold text-white tracking-tighter">ScholarAI</h3>
            <p className="text-xs text-slate-500 max-w-sm leading-relaxed uppercase tracking-widest">
              Developed by <span className="text-blue-400">Nandish Sinha</span> (2026) for <span className="text-white">Sensorspine Pvt. Ltd</span>.
              <br />Beyond the Event Horizon of Detection.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 md:gap-12">
            {[
              { label: "Product", links: ["Features", "Pricing", "Methodology"] },
              { label: "Legal", links: ["Privacy", "Terms", "Security"] },
              { label: "Resources", links: ["Docs", "API", "Status"] },
              { label: "Company", links: ["About", "Contact", "Enterprise"] }
            ].map((col, i) => (
              <div key={i} className="space-y-4">
                <h4 className="text-[10px] font-bold text-white uppercase tracking-widest">{col.label}</h4>
                <ul className="space-y-2">
                  {col.links.map((link, j) => (
                    <li key={j}>
                      <a href="#" className="text-[10px] text-slate-500 hover:text-blue-400 transition-colors uppercase tracking-wider">{link}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-16 pt-8 border-t border-white/5 text-[9px] text-slate-600 uppercase tracking-[0.3em] text-center">
          © 2026 Sensorspine Pvt. Ltd. All systems operational.
        </div>
      </footer>
    </div>
  );
}
