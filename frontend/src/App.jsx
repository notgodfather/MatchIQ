import { useState, useEffect } from 'react';
import { Upload, ArrowRight, Settings2, Database, Search, Library, CheckCircle2, Fingerprint, Zap, Layers } from 'lucide-react';
import PixelSnow from './PixelSnow';
import ParticleText from './ParticleText';
import MappingView from './MappingView';
import ProgressView from './ProgressView';
import ResultsView from './ResultsView';

// Holographic Entity Resolution HUD Animation
function HolographicResolutionHUD() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStage((prev) => (prev + 1) % 3);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative w-full max-w-4xl h-[400px] mx-auto mt-12 mb-16 flex items-center justify-center font-mono text-[11px] perspective-1000">
      
      {/* Decorative HUD Rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
        <div className="w-[600px] h-[600px] border border-emerald-500/30 rounded-full animate-[spin_60s_linear_infinite]"></div>
        <div className="absolute w-[400px] h-[400px] border border-sky-500/30 rounded-full animate-[spin_40s_linear_infinite_reverse]"></div>
      </div>

      {/* Left Data Node */}
      <div className={`absolute transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        stage === 2 ? 'opacity-0 scale-90 blur-xl translate-x-0' : 'opacity-100 scale-100 blur-0 -translate-x-32 md:-translate-x-48'
      } bg-[#040608]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-5 w-72 shadow-[0_0_50px_rgba(0,0,0,0.8)] z-10 transform-gpu`}>
        <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2 text-emerald-400/80 uppercase tracking-widest text-[9px]">
            <Database className="w-3 h-3" /> Source_Alpha
          </div>
          <span className="text-white/30 text-[9px]">ID: A-7892</span>
        </div>
        <div className="space-y-3 text-slate-400">
          <div className="flex justify-between"><span className="text-slate-600">FirstName</span><span className="text-slate-200">Jon</span></div>
          <div className="flex justify-between"><span className="text-slate-600">LastName</span><span className="text-slate-200">Doe</span></div>
          <div className="flex justify-between"><span className="text-slate-600">Contact</span><span className="text-slate-200">j@doe.com</span></div>
          <div className="flex justify-between"><span className="text-slate-600">Phone</span><span className="text-slate-200">555-0192</span></div>
        </div>
      </div>

      {/* Right Data Node */}
      <div className={`absolute transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        stage === 2 ? 'opacity-0 scale-90 blur-xl translate-x-0' : 'opacity-100 scale-100 blur-0 translate-x-32 md:translate-x-48'
      } bg-[#040608]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-5 w-72 shadow-[0_0_50px_rgba(0,0,0,0.8)] z-10 transform-gpu`}>
        <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2 text-sky-400/80 uppercase tracking-widest text-[9px]">
            <Database className="w-3 h-3" /> Source_Beta
          </div>
          <span className="text-white/30 text-[9px]">ID: B-4410</span>
        </div>
        <div className="space-y-3 text-slate-400">
          <div className="flex justify-between"><span className="text-slate-600">Full_Name</span><span className="text-slate-200">Johnathan Doe</span></div>
          <div className="flex justify-between"><span className="text-slate-600">Email_Addr</span><span className="text-slate-200">john.doe@gmail.com</span></div>
          <div className="flex justify-between"><span className="text-slate-600">Mobile</span><span className="text-slate-200">+1-555-0192</span></div>
          <div className="flex justify-between"><span className="text-slate-600">Company</span><span className="text-rose-400/80">NULL</span></div>
        </div>
      </div>

      {/* ML Processing HUD (Stage 1) */}
      <div className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-700 z-0 ${
        stage === 1 ? 'opacity-100 scale-100' : 'opacity-0 scale-110'
      }`}>
        <div className="w-[600px] h-[1px] bg-gradient-to-r from-transparent via-emerald-400/50 to-transparent relative">
           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-black/90 backdrop-blur-md px-4 py-2 border border-white/10 rounded-full text-emerald-400 flex items-center gap-2 shadow-[0_0_30px_rgba(52,211,153,0.15)] uppercase tracking-widest">
             <Zap className="w-3 h-3 text-emerald-400 animate-pulse" /> Neural Match: 99.8%
           </div>
           {/* HUD Scanning Beams */}
           <div className="absolute top-1/2 left-1/4 w-[100px] h-[1px] bg-white -translate-y-1/2 animate-[scan_1s_ease-in-out_infinite_alternate] shadow-[0_0_15px_#fff]"></div>
        </div>
      </div>

      {/* Golden Record (Stage 2) */}
      <div className={`absolute transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        stage === 2 ? 'opacity-100 scale-110 blur-0 translate-y-0' : 'opacity-0 scale-75 blur-2xl translate-y-12'
      } bg-gradient-to-b from-[#0a1118]/95 to-[#040608]/95 backdrop-blur-2xl border border-emerald-500/40 rounded-2xl p-6 w-[340px] shadow-[0_0_80px_rgba(52,211,153,0.15)] z-20`}>
        <div className="absolute -top-px left-1/2 -translate-x-1/2 w-32 h-[1px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent"></div>
        <div className="flex items-center justify-between mb-5 border-b border-emerald-500/20 pb-4">
          <div className="flex items-center gap-2 text-emerald-400 font-bold tracking-widest text-[10px]">
            <Fingerprint className="w-4 h-4" /> GOLDEN_ENTITY
          </div>
          <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2.5 py-1 rounded-sm text-[8px] uppercase tracking-widest shadow-[0_0_10px_rgba(52,211,153,0.2)]">Resolved</span>
        </div>
        <div className="space-y-4 text-[12px] text-slate-300">
          <div className="flex justify-between items-center"><span className="text-slate-600">Name</span><span className="font-medium text-white">Johnathan Doe</span></div>
          <div className="flex justify-between items-center"><span className="text-slate-600">Email</span><span className="text-emerald-300">john.doe@gmail.com</span></div>
          <div className="flex justify-between items-center"><span className="text-slate-600">Phone</span><span className="text-emerald-300">+1-555-0192</span></div>
          <div className="flex justify-between items-center"><span className="text-slate-600">Company</span><span className="text-white">Acme Corp</span></div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [viewState, setViewState] = useState({ name: 'landing', params: {} }); // 'landing', 'workspace', 'mapping', 'progress', 'results'
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [datasetA, setDatasetA] = useState(null);
  const [datasetB, setDatasetB] = useState(null);
  const [uploading, setUploading] = useState(false);

  const setView = (name, params = {}) => setViewState({ name, params });
  const view = viewState.name;

  const handleUpload = async () => {
    if (!fileA || !fileB) return;
    setUploading(true);
    
    try {
      const uploadFile = async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/datasets', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to upload ${file.name}`);
        }
        return await res.json();
      };
      
      // Upload both files in parallel
      const [resA, resB] = await Promise.all([
        uploadFile(fileA),
        uploadFile(fileB)
      ]);
      
      setDatasetA(resA);
      setDatasetB(resB);
      setView('mapping');
    } catch (err) {
      console.error(err);
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  if (view === 'landing') {
    return (
      <div className="w-full min-h-screen bg-[#020202] text-white overflow-hidden relative">
        <div className="fixed inset-0 z-0 pointer-events-none mix-blend-screen opacity-70">
          <PixelSnow 
            color="#34d399"
            flakeSize={0.01}
            minFlakeSize={1.25}
            pixelResolution={200}
            speed={1.25}
            density={0.3}
            direction={125}
            brightness={1}
          />
        </div>
        
        {/* Vignette overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#020202_90%)] z-0 pointer-events-none opacity-90"></div>

        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full px-6 pt-16 animate-fade-in-up pointer-events-auto">
          
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] text-slate-400 text-[10px] uppercase tracking-widest font-mono mb-8 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            System Ready
          </div>
          
          <div className="w-full max-w-5xl h-32 md:h-48 mb-6 mx-auto pointer-events-auto">
            <ParticleText
              text="MatchIQ"
              particleSize={2}
              density={4}
              color="#ffffff"
              highlightColor="#34d399"
              scatter={180}
              gatherDuration={1600}
              stagger={420}
              pointerRepel={40}
              repelRadius={120}
              idleDrift={0.7}
              trigger="hover"
              fontSize="clamp(3rem, 15vw, 9rem)"
              fontWeight={800}
              fontFamily="ui-serif, Georgia, Cambria, Times New Roman, Times, serif"
              glow
            />
          </div>
          
          <p className="text-slate-400 font-light text-lg mb-4 max-w-xl text-center">
            MatchIQ fuses millions of messy records into single, perfect golden entities using advanced machine learning.
          </p>

          <div className="pointer-events-auto">
            <HolographicResolutionHUD />
          </div>

          <button 
            onClick={() => setView('workspace')}
            className="pointer-events-auto group relative flex items-center gap-3 px-8 py-4 bg-white text-black rounded-full font-medium text-sm transition-all duration-500 hover:scale-[1.02] overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-200 to-sky-200 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <span className="relative z-10">Deploy Workspace</span>
            <ArrowRight className="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>
    );
  }

  if (view === 'workspace') {
    return (
      <div className="min-h-screen bg-[#020202] text-slate-300 selection:bg-white/20 relative animate-fade-in-up">
      <div className="fixed inset-0 z-0 mix-blend-screen opacity-20 pointer-events-none">
        <PixelSnow 
          color="#34d399"
          flakeSize={0.01}
          minFlakeSize={1.25}
          pixelResolution={200}
          speed={1.25}
          density={0.3}
          direction={125}
          brightness={1}
        />
      </div>
      <div className="fixed inset-0 bg-black/70 z-0 pointer-events-none backdrop-blur-sm"></div>

      <header className="sticky top-0 z-40 border-b border-white/5 bg-[#020202]/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-white flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.3)]">
              <Layers className="w-3.5 h-3.5 text-black" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-mono tracking-widest uppercase text-white">MatchIQ</span>
          </div>
          <nav className="flex items-center gap-8 text-[11px] uppercase tracking-widest font-mono text-slate-500">
            <button className="text-white">Workspace</button>
            <button className="hover:text-white transition-colors">Mapping</button>
            <button className="hover:text-white transition-colors">Results</button>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-24 relative z-10">
        <div className="mb-20">
          <h1 className="text-4xl md:text-6xl font-serif text-white font-light mb-4 tracking-tight">
            Initialize <i className="text-white/50">Pipeline</i>
          </h1>
          <p className="text-slate-400 font-light text-lg">
            Mount your source datasets to the processing engine.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          <div className="group relative rounded-2xl bg-white/[0.02] border border-white/[0.05] p-10 hover:bg-white/[0.04] transition-all duration-500 overflow-hidden flex flex-col justify-between min-h-[360px] backdrop-blur-md">
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity duration-700">
              <Database className="w-48 h-48 text-white stroke-[0.2]" />
            </div>
            <div className="relative z-10">
              <div className="inline-flex items-center gap-3 px-3 py-1.5 rounded-sm bg-white/5 border border-white/10 text-[10px] uppercase tracking-widest text-white mb-8">
                <Library className="w-3 h-3" /> Master
              </div>
              <h3 className="text-3xl font-serif text-white mb-4">Primary Source</h3>
              <p className="text-sm font-light text-slate-400 max-w-sm leading-relaxed">
                The core authoritative database containing verified entities. This schema acts as the ground truth.
              </p>
            </div>
            <div className="relative z-10 mt-12">
              <input type="file" className="hidden" id="file-a" onChange={(e) => setFileA(e.target.files[0])} accept=".csv" />
              <label htmlFor="file-a" className={`inline-flex items-center justify-center w-full gap-3 px-6 py-4 rounded-lg text-sm cursor-pointer transition-all border ${
                fileA ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-black/50 border-white/10 text-slate-300 hover:bg-white/5 hover:border-white/20'
              }`}>
                {fileA ? <><CheckCircle2 className="w-5 h-5" /> {fileA.name}</> : <><Upload className="w-4 h-4" /> Mount CSV</>}
              </label>
            </div>
          </div>
          
          <div className="group relative rounded-2xl bg-white/[0.02] border border-white/[0.05] p-10 hover:bg-white/[0.04] transition-all duration-500 overflow-hidden flex flex-col justify-between min-h-[360px] backdrop-blur-md">
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity duration-700">
              <Database className="w-48 h-48 text-white stroke-[0.2]" />
            </div>
            <div className="relative z-10">
              <div className="inline-flex items-center gap-3 px-3 py-1.5 rounded-sm bg-white/5 border border-white/10 text-[10px] uppercase tracking-widest text-white mb-8">
                <Settings2 className="w-3 h-3" /> External
              </div>
              <h3 className="text-3xl font-serif text-white mb-4">Candidate Source</h3>
              <p className="text-sm font-light text-slate-400 max-w-sm leading-relaxed">
                The messy, secondary dataset to be deduplicated, linked, and merged into the primary source.
              </p>
            </div>
            <div className="relative z-10 mt-12">
              <input type="file" className="hidden" id="file-b" onChange={(e) => setFileB(e.target.files[0])} accept=".csv" />
              <label htmlFor="file-b" className={`inline-flex items-center justify-center w-full gap-3 px-6 py-4 rounded-lg text-sm cursor-pointer transition-all border ${
                fileB ? 'bg-sky-500/10 border-sky-500/30 text-sky-400' : 'bg-black/50 border-white/10 text-slate-300 hover:bg-white/5 hover:border-white/20'
              }`}>
                {fileB ? <><CheckCircle2 className="w-5 h-5" /> {fileB.name}</> : <><Upload className="w-4 h-4" /> Mount CSV</>}
              </label>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-4">
          <button 
            onClick={handleUpload}
            disabled={!fileA || !fileB || uploading}
            className={`px-10 py-4 rounded-lg text-sm font-medium tracking-wider uppercase flex items-center gap-4 transition-all duration-500 ${
              (!fileA || !fileB) 
                ? 'bg-white/5 text-slate-600 cursor-not-allowed border border-white/5' 
                : 'bg-white text-black hover:scale-[1.02] shadow-[0_0_40px_rgba(255,255,255,0.15)]'
            }`}
          >
            {uploading ? (
              <span className="flex items-center gap-3">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processing Stream...
              </span>
            ) : (
              <>Execute Engine <ArrowRight className="w-4 h-4" /></>
            )}
          </button>
        </div>
      </main>
    </div>
    );
  }

  if (view === 'mapping') {
    return (
      <MappingView 
        datasetA={datasetA} 
        datasetB={datasetB} 
        setView={setView} 
      />
    );
  }

  if (view === 'progress') {
    return (
      <ProgressView 
        jobId={viewState.params.jobId}
        setView={setView}
      />
    );
  }

  if (view === 'results') {
    return (
      <ResultsView 
        jobId={viewState.params.jobId}
        setView={setView}
      />
    );
  }

  return null; // fallback
}

export default App;
