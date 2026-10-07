import { useState, useEffect } from 'react';
import { Layers, Loader2, Database, ShieldCheck, Cpu, CheckCircle2 } from 'lucide-react';
import PixelSnow from './PixelSnow';

export default function ProgressView({ jobId, setView }) {
  const [job, setJob] = useState(null);

  useEffect(() => {
    if (!jobId) return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (res.ok) {
          const data = await res.json();
          setJob(data);
          if (data.status === 'COMPLETED') {
            clearInterval(interval);
            setTimeout(() => {
              setView('results', { jobId });
            }, 1000);
          } else if (data.status === 'FAILED') {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error(err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId, setView]);

  const getStageMessage = (stage) => {
    switch (stage?.toLowerCase()) {
      case 'initializing': return 'Booting Neural Engine...';
      case 'normalizing': return 'Normalizing Data (Formatting, Aliases)...';
      case 'blocking': return 'Generating Candidate Pairs (Blocking)...';
      case 'features': return 'Extracting Machine Learning Features...';
      case 'scoring': return 'Applying GBM Model & Thresholds...';
      case 'resolution': return 'Resolving Golden Entities...';
      case 'completed': return 'Pipeline Completed Successfully.';
      default: return `Processing Stage: ${stage || 'Starting'}...`;
    }
  };

  const progress = job?.progress || 0;

  return (
    <div className="min-h-screen bg-[#020202] text-slate-300 selection:bg-white/20 relative animate-fade-in-up flex flex-col">
      <div className="fixed inset-0 z-0 mix-blend-screen opacity-10 pointer-events-none">
        <PixelSnow color="#34d399" density={0.15} speed={2} />
      </div>

      <header className="sticky top-0 z-40 border-b border-white/5 bg-[#020202]/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-white flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.3)]">
              <Layers className="w-3.5 h-3.5 text-black" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-mono tracking-widest uppercase text-white">MatchIQ</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] uppercase font-mono tracking-widest text-emerald-500">Pipeline Active</span>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center relative z-10 p-6">
        <div className="w-full max-w-xl bg-white/[0.02] border border-white/[0.05] rounded-3xl p-10 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          
          {/* Subtle animated background glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[150%] h-[150%] bg-[radial-gradient(ellipse_at_center,rgba(52,211,153,0.03)_0%,transparent_50%)] animate-[spin_10s_linear_infinite] pointer-events-none"></div>

          <div className="text-center mb-10 relative z-10">
            {job?.status === 'FAILED' ? (
              <>
                <div className="w-20 h-20 bg-rose-500/10 border border-rose-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <ShieldCheck className="w-8 h-8 text-rose-500" />
                </div>
                <h2 className="text-3xl font-serif text-white mb-2">Pipeline Failed</h2>
                <p className="text-rose-400 font-mono text-xs">{job.error || 'Unknown error occurred.'}</p>
              </>
            ) : job?.status === 'COMPLETED' ? (
              <>
                <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(52,211,153,0.2)]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
                <h2 className="text-3xl font-serif text-white mb-2">Resolution Complete</h2>
                <p className="text-slate-400 font-light text-sm">Preparing dashboard...</p>
              </>
            ) : (
              <>
                <div className="w-20 h-20 bg-white/5 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                  <div className="absolute inset-0 rounded-full border-2 border-emerald-500/30 border-t-transparent animate-[spin_3s_linear_infinite]"></div>
                </div>
                <h2 className="text-3xl font-serif text-white mb-2">Processing Data</h2>
                <p className="text-slate-400 font-light text-sm h-5">{getStageMessage(job?.stage)}</p>
              </>
            )}
          </div>

          <div className="relative z-10">
            <div className="flex justify-between text-xs font-mono tracking-widest uppercase mb-3 text-slate-500">
              <span>Progress</span>
              <span className="text-emerald-400">{Math.round(progress)}%</span>
            </div>
            
            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-sky-400 rounded-full transition-all duration-700 ease-out relative"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute top-0 right-0 bottom-0 left-0 bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.4),transparent)] -translate-x-full animate-[scan_1.5s_ease-in-out_infinite]"></div>
              </div>
            </div>
          </div>

          <div className="mt-10 grid grid-cols-3 gap-4 relative z-10 opacity-60">
             <div className="flex flex-col items-center gap-2 text-center">
                <Database className={`w-4 h-4 ${progress > 10 ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span className="text-[9px] uppercase font-mono tracking-widest text-slate-500">Index</span>
             </div>
             <div className="flex flex-col items-center gap-2 text-center">
                <Cpu className={`w-4 h-4 ${progress > 50 ? 'text-sky-400' : 'text-slate-600'}`} />
                <span className="text-[9px] uppercase font-mono tracking-widest text-slate-500">ML Engine</span>
             </div>
             <div className="flex flex-col items-center gap-2 text-center">
                <ShieldCheck className={`w-4 h-4 ${progress >= 100 ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span className="text-[9px] uppercase font-mono tracking-widest text-slate-500">Verify</span>
             </div>
          </div>

        </div>
      </main>
    </div>
  );
}
