import { useState, useEffect } from 'react';
import { Layers, User, Phone, Mail, MapPin, Building2, Map, Hash, Calendar, Briefcase, ArrowRight, CheckCircle2 } from 'lucide-react';
import PixelSnow from './PixelSnow';

const CANONICAL_FIELDS = [
  { id: 'name', label: 'Name', icon: User, description: 'Full name, given name, or surname' },
  { id: 'phone', label: 'Phone Number', icon: Phone, description: 'Mobile or landline' },
  { id: 'email', label: 'Email', icon: Mail, description: 'Email address' },
  { id: 'address', label: 'Address', icon: MapPin, description: 'Street address' },
  { id: 'city', label: 'City / Suburb', icon: Building2, description: 'City or town' },
  { id: 'state', label: 'State / Province', icon: Map, description: 'State or territory' },
  { id: 'postcode', label: 'Postcode', icon: Hash, description: 'Postal code or PIN' },
  { id: 'dob', label: 'Date of Birth', icon: Calendar, description: 'Birth date' },
  { id: 'company', label: 'Company', icon: Briefcase, description: 'Company name' },
];

export default function MappingView({ datasetA, datasetB, setView }) {
  const [mapping, setMapping] = useState({});
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    const colsA = Object.keys(datasetA?.profile_data?.dtypes || {});
    const colsB = Object.keys(datasetB?.profile_data?.dtypes || {});

    const guessMapping = (columns) => {
      const guesses = { name: [], phone: [], email: [], address: [], city: [], state: [], postcode: [], dob: [], company: [] };
      columns.forEach(col => {
        const c = col.toLowerCase().replace(/[^a-z0-9]/g, '');
        if (c.includes('name') && !c.includes('company')) guesses.name.push(col);
        else if (c.includes('phone') || c.includes('mobile') || c.includes('contact')) guesses.phone.push(col);
        else if (c.includes('email') || c.includes('mail')) guesses.email.push(col);
        else if (c.includes('address') || c.includes('street')) guesses.address.push(col);
        else if (c.includes('city') || c.includes('suburb') || c.includes('town')) guesses.city.push(col);
        else if (c.includes('state') || c.includes('province')) guesses.state.push(col);
        else if (c.includes('postcode') || c.includes('zip') || c.includes('pin')) guesses.postcode.push(col);
        else if (c.includes('dob') || c.includes('birth')) guesses.dob.push(col);
        else if (c.includes('company') || c.includes('org') || c.includes('business')) guesses.company.push(col);
      });
      return guesses;
    };

    const guessedA = guessMapping(colsA);
    const guessedB = guessMapping(colsB);

    const initialMapping = {};
    CANONICAL_FIELDS.forEach(f => {
      initialMapping[f.id] = { 
        a: guessedA[f.id] || [], 
        b: guessedB[f.id] || [] 
      };
    });
    setMapping(initialMapping);
  }, [datasetA, datasetB]);

  const handleSelect = (fieldId, side, e) => {
    const selected = Array.from(e.target.selectedOptions, option => option.value);
    setMapping(prev => ({
      ...prev,
      [fieldId]: {
        ...prev[fieldId],
        [side]: selected
      }
    }));
  };

  const handleStartJob = async () => {
    setStarting(true);
    const cleanMapping = {};
    Object.keys(mapping).forEach(key => {
      const { a, b } = mapping[key];
      if (a.length > 0 || b.length > 0) {
        cleanMapping[key] = { a, b };
      }
    });

    try {
      const payload = {
        dataset_a_id: datasetA.id,
        dataset_b_id: datasetB.id,
        mapping_config: cleanMapping,
        model_id: "baseline"
      };

      const res = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
         const errorData = await res.json().catch(() => ({}));
         throw new Error(errorData.detail || 'Failed to start job');
      }

      const job = await res.json();
      console.log("Job started:", job);
      // Transition to progress view
      setView('progress', { jobId: job.id });
      
    } catch (err) {
      console.error(err);
      alert('Job failed to start: ' + err.message);
    } finally {
      setStarting(false);
    }
  };

  const colsA = Object.keys(datasetA?.profile_data?.dtypes || {});
  const colsB = Object.keys(datasetB?.profile_data?.dtypes || {});

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
            <button className="text-white">Mapping</button>
            <button className="hover:text-white transition-colors">Results</button>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-24 relative z-10">
        <div className="mb-16">
          <h1 className="text-4xl md:text-5xl font-serif text-white font-light mb-4 tracking-tight">
            Schema <i className="text-white/50">Mapping</i>
          </h1>
          <p className="text-slate-400 font-light text-lg">
            Map your raw columns to MatchIQ's canonical fields. Hold Cmd/Ctrl to select multiple.
          </p>
        </div>
        
        <div className="grid grid-cols-1 gap-6 mb-16">
          {CANONICAL_FIELDS.map(field => {
            const Icon = field.icon;
            return (
              <div key={field.id} className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 flex flex-col md:flex-row gap-6 md:items-center backdrop-blur-md hover:bg-white/[0.03] transition-colors">
                <div className="w-full md:w-1/3">
                  <div className="flex items-center gap-3 text-white mb-1">
                    <Icon className="w-4 h-4 text-emerald-400" />
                    <span className="font-mono uppercase tracking-widest text-sm">{field.label}</span>
                  </div>
                  <p className="text-slate-500 text-xs mt-2 font-light pr-4">{field.description}</p>
                </div>
                
                <div className="w-full md:w-1/3">
                  <label className="block text-[10px] text-emerald-400/80 uppercase tracking-widest mb-2 font-mono">Primary Source</label>
                  <select 
                    multiple 
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-slate-300 focus:border-emerald-500/50 outline-none min-h-[90px] font-mono"
                    value={mapping[field.id]?.a || []}
                    onChange={(e) => handleSelect(field.id, 'a', e)}
                  >
                    {colsA.map(col => (
                      <option key={col} value={col} className="checked:bg-emerald-500/20 checked:text-emerald-300 py-1 px-2 rounded-sm mb-1">{col}</option>
                    ))}
                  </select>
                </div>

                <div className="w-full md:w-1/3">
                  <label className="block text-[10px] text-sky-400/80 uppercase tracking-widest mb-2 font-mono">Candidate Source</label>
                  <select 
                    multiple 
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-slate-300 focus:border-sky-500/50 outline-none min-h-[90px] font-mono"
                    value={mapping[field.id]?.b || []}
                    onChange={(e) => handleSelect(field.id, 'b', e)}
                  >
                    {colsB.map(col => (
                      <option key={col} value={col} className="checked:bg-sky-500/20 checked:text-sky-300 py-1 px-2 rounded-sm mb-1">{col}</option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end mb-24">
          <button 
            onClick={handleStartJob}
            disabled={starting}
            className={`px-10 py-4 rounded-lg text-sm font-medium tracking-wider uppercase flex items-center gap-4 transition-all duration-500 ${
              starting 
                ? 'bg-white/5 text-slate-600 cursor-not-allowed border border-white/5' 
                : 'bg-white text-black hover:scale-[1.02] shadow-[0_0_40px_rgba(255,255,255,0.15)]'
            }`}
          >
            {starting ? (
              <span className="flex items-center gap-3">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Deploying Job...
              </span>
            ) : (
              <>Start Engine <CheckCircle2 className="w-4 h-4" /></>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
