import { useState, useEffect } from 'react';
import { Layers, CheckCircle2, AlertCircle, Download, FileText, Activity, Database, Check, X, ShieldAlert } from 'lucide-react';
import PixelSnow from './PixelSnow';

export default function ResultsView({ jobId, setView }) {
  const [job, setJob] = useState(null);
  const [results, setResults] = useState([]);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'review'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    
    Promise.all([
      fetch(`/api/jobs/${jobId}`).then(r => r.json()),
      fetch(`/api/jobs/${jobId}/results?page_size=200`).then(r => r.json())
    ]).then(([jobData, resultsData]) => {
      setJob(jobData);
      setResults(resultsData || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [jobId]);

  const reviewResults = results.filter(r => r.decision === 'REVIEW');
  const displayResults = activeTab === 'all' ? results : reviewResults;

  const handleExport = () => {
    window.location.href = `/api/jobs/${jobId}/export?type=all`;
  };

  const handleReviewAction = async (pairId, label) => {
    try {
      await fetch(`/api/jobs/${jobId}/reviews?pair_id=${pairId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label })
      });
      // Optimistically update the UI
      setResults(prev => prev.map(r => 
        r.id === pairId ? { ...r, decision: label } : r
      ));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-[#020202] text-slate-300 selection:bg-white/20 relative animate-fade-in-up">
      <div className="fixed inset-0 z-0 mix-blend-screen opacity-10 pointer-events-none">
        <PixelSnow color="#34d399" density={0.1} />
      </div>
      
      <header className="sticky top-0 z-40 border-b border-white/5 bg-[#020202]/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-white flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.3)]">
              <Layers className="w-3.5 h-3.5 text-black" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-mono tracking-widest uppercase text-white">MatchIQ</span>
          </div>
          <nav className="flex items-center gap-8 text-[11px] uppercase tracking-widest font-mono text-slate-500">
            <button className="hover:text-white transition-colors" onClick={() => setView('workspace')}>Workspace</button>
            <button className="hover:text-white transition-colors">Mapping</button>
            <button className="text-white">Results</button>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-12 relative z-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <h1 className="text-4xl font-serif text-white font-light tracking-tight mb-2">
              Entity <i className="text-white/50">Resolution</i>
            </h1>
            <p className="text-slate-400 font-light">
              Machine Learning pipeline complete. Review the golden records.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={handleExport}
              className="px-6 py-2.5 rounded-lg border border-white/10 hover:bg-white/5 transition-colors flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-slate-300"
            >
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
        </div>
        
        {/* Analytics Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 backdrop-blur-md">
            <div className="flex items-center gap-2 text-slate-500 mb-4">
              <Database className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Candidate Pairs</span>
            </div>
            <div className="text-4xl font-light text-white font-serif">{job?.stats?.total_candidates?.toLocaleString() || '-'}</div>
          </div>
          
          <div className="bg-emerald-500/[0.03] border border-emerald-500/[0.1] rounded-2xl p-6 backdrop-blur-md">
            <div className="flex items-center gap-2 text-emerald-500/80 mb-4">
              <CheckCircle2 className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Auto-Matched</span>
            </div>
            <div className="text-4xl font-light text-emerald-400 font-serif">{job?.stats?.auto_matches?.toLocaleString() || '-'}</div>
          </div>
          
          <div className="bg-amber-500/[0.03] border border-amber-500/[0.1] rounded-2xl p-6 backdrop-blur-md">
            <div className="flex items-center gap-2 text-amber-500/80 mb-4">
              <ShieldAlert className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Needs Review</span>
            </div>
            <div className="text-4xl font-light text-amber-400 font-serif">{job?.stats?.reviews_needed?.toLocaleString() || '-'}</div>
          </div>

          <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 backdrop-blur-md">
            <div className="flex items-center gap-2 text-slate-500 mb-4">
              <Activity className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Model Confidence</span>
            </div>
            <div className="text-4xl font-light text-sky-400 font-serif">High</div>
          </div>
        </div>

        {/* Results Table Section */}
        <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl backdrop-blur-md overflow-hidden flex flex-col h-[600px]">
          
          {/* Tabs */}
          <div className="flex items-center border-b border-white/[0.05] px-6">
            <button 
              onClick={() => setActiveTab('all')}
              className={`px-4 py-4 text-xs font-mono uppercase tracking-widest transition-colors border-b-2 ${
                activeTab === 'all' ? 'border-emerald-400 text-emerald-400' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              All Matches
            </button>
            <button 
              onClick={() => setActiveTab('review')}
              className={`px-4 py-4 text-xs font-mono uppercase tracking-widest transition-colors border-b-2 flex items-center gap-2 ${
                activeTab === 'review' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              Review Queue 
              {job?.stats?.reviews_needed > 0 && (
                <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[9px]">{job.stats.reviews_needed}</span>
              )}
            </button>
          </div>

          {/* Table */}
          <div className="flex-1 overflow-auto p-6">
            {loading ? (
              <div className="flex items-center justify-center h-full text-slate-500 font-mono text-xs uppercase">Loading records...</div>
            ) : displayResults.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-4">
                <FileText className="w-12 h-12 opacity-20" />
                <span className="font-mono text-xs uppercase tracking-widest">No records found.</span>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.05]">
                    <th className="pb-3 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-normal">Primary ID</th>
                    <th className="pb-3 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-normal">Candidate ID</th>
                    <th className="pb-3 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-normal">Confidence</th>
                    <th className="pb-3 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-normal">Status</th>
                    {activeTab === 'review' && (
                      <th className="pb-3 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-normal text-right">Action</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {displayResults.map((r, i) => (
                    <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                      <td className="py-4 text-sm font-light text-slate-300">{r.record_a_id}</td>
                      <td className="py-4 text-sm font-light text-slate-300">{r.record_b_id}</td>
                      <td className="py-4 text-sm">
                        <div className="flex items-center gap-3">
                          <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${r.probability > 0.8 ? 'bg-emerald-500' : r.probability > 0.4 ? 'bg-amber-500' : 'bg-rose-500'}`}
                              style={{ width: `${r.probability * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-xs text-slate-400">{(r.probability * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="py-4">
                        <span className={`px-2.5 py-1 rounded-sm text-[9px] uppercase tracking-widest font-mono border ${
                          r.decision === 'MATCH' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                          r.decision === 'REVIEW' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                          'bg-rose-500/10 border-rose-500/20 text-rose-400'
                        }`}>
                          {r.decision}
                        </span>
                      </td>
                      {activeTab === 'review' && (
                        <td className="py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => handleReviewAction(r.id, 'MATCH')} className="w-8 h-8 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 flex items-center justify-center transition-colors">
                              <Check className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleReviewAction(r.id, 'NON_MATCH')} className="w-8 h-8 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 flex items-center justify-center transition-colors">
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
