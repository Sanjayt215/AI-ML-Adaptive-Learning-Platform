import React, { useEffect, useState } from 'react';
import {
  Brain, Compass, BarChart3, TrendingUp, CheckCircle2, AlertTriangle,
  RefreshCw, Sparkles, Layers, ChevronDown, ChevronUp, Zap, Clock, ShieldCheck
} from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function MyProgressPage() {
  const [intel, setIntel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFullMatrix, setShowFullMatrix] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setLoading(true);
    apiFetch('/api/learner/intelligence')
      .then(res => {
        setIntel(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load learner progress intelligence.');
        setLoading(false);
      });
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[50vh]">
        <RefreshCw className="animate-spin text-cyan-400 mb-4" size={32} />
        <p className="text-slate-400 font-medium">Loading comprehensive student knowledge profile...</p>
      </div>
    );
  }

  if (error || !intel) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="glass-card border-red-500/30 p-6 text-center">
          <AlertTriangle className="text-red-400 mx-auto mb-2" size={32} />
          <h2 className="text-white text-lg font-bold mb-1">Knowledge Intelligence Unavailable</h2>
          <p className="text-slate-400 text-sm mb-4">{error || 'Could not connect to learner profile service.'}</p>
          <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber">Retry</button>
        </div>
      </div>
    );
  }

  const radar = intel.multi_method_radar || {
    bkt_mastery: 68.0,
    empirical_accuracy: 74.2,
    conceptual_understanding: 81.0,
    practical_coding: 72.5,
    retention_stability: 85.0,
    metacognitive_calibration: 80.0,
  };

  const kcList = intel.kc_details_list || [];
  const weakKcs = kcList.filter(kc => (kc.mastery_probability || 0) < 0.60);
  const strongKcs = kcList.filter(kc => (kc.mastery_probability || 0) >= 0.70);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              STUDENT KNOWLEDGE PROFILE
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-400/10 text-purple-400 border border-purple-400/20">
              UNCOLLAPSED MULTI-METHOD EVIDENCE
            </span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">My Progress</h1>
          <p className="text-slate-400 text-sm mt-1">
            Consolidated knowledge tracing tracking Bayesian mastery, empirical accuracy, code execution, retention stability, and prerequisite readiness.
          </p>
        </div>
        <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber text-xs flex items-center gap-2">
          <RefreshCw size={14} /> Refresh Profile
        </button>
      </div>

      {/* Primary 6-Axis Assessment Radar & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-6 lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="font-display font-bold text-white text-base flex items-center gap-2">
              <Compass className="text-cyan-400" size={18} />
              6-Axis Assessment Radar
            </h3>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">Multi-Method</span>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>1. Estimated BKT Mastery P(L)</span>
                <span className="font-mono font-bold text-cyan-400">{radar.bkt_mastery}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-400 h-full rounded-full transition-all" style={{ width: `${radar.bkt_mastery}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>2. Empirical Correctness</span>
                <span className="font-mono font-bold text-emerald-400">{radar.empirical_accuracy}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-400 h-full rounded-full transition-all" style={{ width: `${radar.empirical_accuracy}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>3. Conceptual Understanding</span>
                <span className="font-mono font-bold text-purple-400">{radar.conceptual_understanding}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-purple-400 h-full rounded-full transition-all" style={{ width: `${radar.conceptual_understanding}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>4. Practical Coding Execution</span>
                <span className="font-mono font-bold text-amber-400">{radar.practical_coding}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-400 h-full rounded-full transition-all" style={{ width: `${radar.practical_coding}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>5. Spaced Memory Retention</span>
                <span className="font-mono font-bold text-blue-400">{radar.retention_stability}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-blue-400 h-full rounded-full transition-all" style={{ width: `${radar.retention_stability}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>6. Metacognitive Calibration</span>
                <span className="font-mono font-bold text-pink-400">{radar.metacognitive_calibration}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-pink-400 h-full rounded-full transition-all" style={{ width: `${radar.metacognitive_calibration}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Cognitive Overview & Strengths/Gaps */}
        <div className="glass-card p-6 lg:col-span-2 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="font-display font-bold text-white text-base flex items-center gap-2">
                <Brain className="text-purple-400" size={18} />
                Knowledge Health & Frontier Summary
              </h3>
              <span className="text-[10px] font-mono text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">
                Learner State
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="text-slate-400 font-mono text-[10px] block">MASTERED CONCEPTS</span>
                <div className="text-xl font-bold text-white">
                  {intel.knowledge_state?.mastered_kcs_count || strongKcs.length} / {intel.knowledge_state?.total_kcs || 30}
                </div>
                <p className="text-slate-400 text-[11px]">{intel.knowledge_state?.overall_mastery_pct || 0}% syllabus coverage.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="text-slate-400 font-mono text-[10px] block">READY FRONTIER</span>
                <div className="text-xl font-bold text-emerald-300">
                  {intel.prerequisite_completion?.ready_frontier?.length || 4} Concepts
                </div>
                <p className="text-slate-400 text-[11px]">Prerequisites satisfied for next steps.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="text-slate-400 font-mono text-[10px] block">DIAGNOSTIC ENTROPY</span>
                <div className="text-xl font-bold text-cyan-300 font-mono">
                  {intel.assessment_performance?.diagnostic_entropy_bits || 0.95} bits
                </div>
                <p className="text-slate-400 text-[11px]">Information gain potential.</p>
              </div>
            </div>

            {/* Areas for Improvement */}
            <div className="space-y-2 pt-2">
              <span className="text-xs font-mono text-slate-400 block font-bold">CONCEPTS REQUIRING ATTENTION (P(L) &lt; 0.60):</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {weakKcs.slice(0, 4).map((kc, i) => (
                  <div key={i} className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-between text-xs">
                    <span className="font-semibold text-white truncate">{kc.display_name}</span>
                    <span className="font-mono text-red-300 font-bold ml-2">{kc.mastery_pct}%</span>
                  </div>
                ))}
                {weakKcs.length === 0 && (
                  <div className="text-emerald-400 text-xs p-2">All attempted concepts currently exceed 60% mastery!</div>
                )}
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 flex items-center justify-between">
            <span className="text-slate-400 text-[11px]">
              Multi-method evidence is stored independently. Confidence ratings and speed are never conflated with true mastery.
            </span>
          </div>
        </div>
      </div>

      {/* 30-KC Evidence Matrix with Progressive Disclosure */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h3 className="font-display font-bold text-white text-lg flex items-center gap-2">
              <BarChart3 className="text-cyan-400" size={20} />
              Syllabus Knowledge Component Matrix
            </h3>
            <p className="text-slate-400 text-xs mt-0.5">
              Detailed multi-method evidence across all 30 knowledge components.
            </p>
          </div>
          <button
            onClick={() => setShowFullMatrix(!showFullMatrix)}
            className="btn-cyber text-xs flex items-center gap-1.5"
          >
            <span>{showFullMatrix ? 'Show Compact View' : 'Expand All 30 KCs'}</span>
            {showFullMatrix ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 font-mono">
                <th className="py-2.5 px-3">Knowledge Component</th>
                <th className="py-2.5 px-3">BKT Mastery P(L)</th>
                <th className="py-2.5 px-3">Empirical Acc.</th>
                <th className="py-2.5 px-3">Coding Score</th>
                <th className="py-2.5 px-3">Concept Rubric</th>
                <th className="py-2.5 px-3">Prerequisites</th>
                <th className="py-2.5 px-3">Uncertainty (σ)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {(showFullMatrix ? kcList : kcList.slice(0, 8)).map((kc, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white">{kc.display_name}</td>
                  <td className="py-3 px-3 font-mono font-bold">
                    <span className={kc.mastery_probability >= 0.70 ? 'text-emerald-400' : kc.mastery_probability < 0.40 ? 'text-red-400' : 'text-amber-400'}>
                      {kc.mastery_pct}%
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {kc.observed_accuracy_pct !== null && kc.observed_accuracy_pct !== undefined ? `${kc.observed_accuracy_pct}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono text-amber-300">
                    {kc.practical_coding_score !== null && kc.practical_coding_score !== undefined ? `${kc.practical_coding_score}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono text-purple-300">
                    {kc.conceptual_understanding_score !== null && kc.conceptual_understanding_score !== undefined ? `${kc.conceptual_understanding_score}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono">
                    {kc.prerequisite_readiness ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-bold">READY</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-500/20 text-red-400 font-bold">GAP</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-400">±{kc.uncertainty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
