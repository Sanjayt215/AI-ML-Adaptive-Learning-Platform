import React, { useEffect, useState } from 'react';
import { Brain, Cpu, Shield, Award, BarChart3, Activity, Zap, CheckCircle2, AlertTriangle, ArrowRight, RefreshCw, Sparkles, Sliders } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function RLIntelligencePage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setLoading(true);
    apiFetch('/api/rl/intelligence')
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load RL intelligence telemetry.');
        setLoading(false);
      });
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[50vh]">
        <RefreshCw className="animate-spin text-cyan-400 mb-4" size={32} />
        <p className="text-slate-400 font-medium">Aggregating RL agent telemetry and BKT observation vectors...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="glass-card border-red-500/30 p-6 text-center">
          <AlertTriangle className="text-red-400 mx-auto mb-2" size={32} />
          <h2 className="text-white text-lg font-bold mb-1">Intelligence Service Offline</h2>
          <p className="text-slate-400 text-sm mb-4">{error || 'Unable to retrieve RL agent metrics.'}</p>
          <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber">Retry Telemetry</button>
        </div>
      </div>
    );
  }

  const { live_learner_state: intel, policy_laboratory: lab, reward_analytics: reward, benchmark_comparison: benchmarks, safety_and_invariants: safety, diagnostic_entropy: entropy } = data;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              RESEARCH & RUNTIME TELEMETRY
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-400/10 text-purple-400 border border-purple-400/20">
              99-DIM OBS · 52 ACTIONS
            </span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">RL Intelligence Center</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time inspection of Bayesian Knowledge Tracing, action masking, multi-objective reward decomposition, and policy benchmarks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber text-xs flex items-center gap-2">
            <RefreshCw size={14} /> Refresh Live Telemetry
          </button>
        </div>
      </div>

      {/* Section A: Live Learner State */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          <h2 className="text-xl font-display font-bold text-white">A. Live Learner Knowledge State</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-card p-5">
            <span className="text-xs font-mono text-slate-400 block mb-1">OVERALL BKT MASTERY</span>
            <div className="text-3xl font-display font-bold text-cyan-400">
              {intel?.knowledge_state?.overall_mastery_pct || 0}%
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Mean mastery across all 30 syllabus knowledge components.
            </p>
          </div>

          <div className="glass-card p-5">
            <span className="text-xs font-mono text-slate-400 block mb-1">KC STATUS BREAKDOWN</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-400">{intel?.knowledge_state?.mastered_kcs_count || 0}</span>
              <span className="text-xs text-slate-400">Mastered</span>
              <span className="text-slate-600">/</span>
              <span className="text-2xl font-bold text-amber-400">{intel?.knowledge_state?.learning_kcs_count || 0}</span>
              <span className="text-xs text-slate-400">Learning</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Prerequisite mastery threshold calibrated at P(L) ≥ 0.70.
            </p>
          </div>

          <div className="glass-card p-5">
            <span className="text-xs font-mono text-slate-400 block mb-1">DIAGNOSTIC ENTROPY (EIG)</span>
            <div className="text-3xl font-display font-bold text-purple-400">
              {intel?.assessment_performance?.diagnostic_entropy_bits || 0.95} <span className="text-sm font-normal text-slate-400">bits</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Expected information gain for questions near P(K) ≈ 0.50 boundary.
            </p>
          </div>

          <div className="glass-card p-5">
            <span className="text-xs font-mono text-slate-400 block mb-1">MEMORY RETENTION R(t)</span>
            <div className="text-3xl font-display font-bold text-emerald-400">
              {intel?.retention_estimates?.average_retention_pct || 88}%
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Half-life decay model R(t) = 2^(-Δt/S). {intel?.retention_estimates?.due_reviews_count || 0} reviews currently due.
            </p>
          </div>
        </div>
      </div>

      {/* Section B & C: Recommendation Intelligence & RL Policy Laboratory */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policy Laboratory */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="text-cyan-400" size={18} />
              <h3 className="font-display font-bold text-white text-base">B. RL Policy Laboratory</h3>
            </div>
            <span className="badge-chip text-[10px] bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              Dual Architecture
            </span>
          </div>

          <div className="space-y-4 text-xs">
            {/* Production Policy */}
            <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">1. Production Policy: Composite Adaptive</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 font-bold">
                  ACTIVE
                </span>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Rule-scaffolded Bayesian Knowledge Tracing with DAG topological action masking, difficulty hysteresis controller, and spaced repetition.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {lab?.production?.components?.map((c, i) => (
                  <span key={i} className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 text-slate-300">
                    {c}
                  </span>
                ))}
              </div>
            </div>

            {/* Experimental Policy */}
            <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">2. Experimental Policy: Dueling Double DQN</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-400 font-bold">
                  DISABLED BY DEFAULT
                </span>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Deep Q-Network with dueling streams separating State-Value V(s) and Advantage A(s, a). Gated by safety invariants in shadow evaluation mode.
              </p>
              <div className="font-mono text-[11px] text-purple-300 space-y-1 pt-1">
                <div>Observation Space: 99 features (30 BKT + 30 counts + 30 prereqs + 9 context)</div>
                <div>Action Space: Discrete 52 canonical actions with topological masking</div>
                <div>Checkpoint: {lab?.experimental?.checkpoint || 'models/dqn/dueling_dqn_final.pt'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Reward Analytics */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="text-purple-400" size={18} />
              <h3 className="font-display font-bold text-white text-base">C. Multi-Objective Reward Decomposition</h3>
            </div>
            <span className="badge-chip text-[10px] bg-purple-400/10 text-purple-400 border border-purple-400/20">
              Transparent RL
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-white/5 font-mono text-[11px] text-cyan-300">
              {reward?.formula || 'R_t = R_mastery + R_info + R_match + R_penalty + R_invalid + R_step'}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-slate-300 font-medium">1. Mastery Improvement (R_mastery)</span>
                <span className="font-mono font-bold text-emerald-400">+{reward?.recent_sample_breakdown?.r_mastery_gain || '0.00'}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-slate-300 font-medium">2. Information Gain / Entropy Reduction (R_info)</span>
                <span className="font-mono font-bold text-purple-400">+{reward?.recent_sample_breakdown?.r_info_gain || '0.45'}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-slate-300 font-medium">3. Zone of Proximal Development Match (R_match)</span>
                <span className="font-mono font-bold text-cyan-400">+{reward?.recent_sample_breakdown?.r_challenge_match || '0.35'}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-slate-300 font-medium">4. Frustration / Repeated Mistake Penalty (R_penalty)</span>
                <span className="font-mono font-bold text-red-400">{reward?.recent_sample_breakdown?.r_failure_penalty || '0.00'}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-slate-300 font-medium">5. Pedagogical Pacing Step Cost (R_step)</span>
                <span className="font-mono font-bold text-slate-400">{reward?.recent_sample_breakdown?.r_step_cost || '-0.05'}</span>
              </div>
              <div className="flex justify-between items-center py-2 pt-3 border-t border-white/10 font-bold">
                <span className="text-white text-sm">Net Scalar Reward (R_t)</span>
                <span className="font-mono text-base text-cyan-300">
                  {reward?.recent_sample_breakdown?.net_scalar_reward || '0.75'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section D: Policy Benchmark Comparison */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Award className="text-amber-400" size={20} />
              <h3 className="font-display font-bold text-white text-lg">D. Empirical 10-Policy Benchmark Comparison</h3>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">
              Comparative evaluation across 500 simulated learner trajectories from Phase 7 benchmark suite.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Source: reports/phase7_policy_comparison.json</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 font-mono">
                <th className="py-2.5 px-3">Policy Name</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Mean Reward</th>
                <th className="py-2.5 px-3">95% CI</th>
                <th className="py-2.5 px-3">Accuracy</th>
                <th className="py-2.5 px-3">Net Mastery Gain</th>
                <th className="py-2.5 px-3">BKT MAE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {benchmarks?.map((p, i) => (
                <tr key={i} className={`hover:bg-white/5 transition-colors ${p.is_production ? 'bg-cyan-500/10 font-medium' : ''}`}>
                  <td className="py-3 px-3 font-semibold text-white flex items-center gap-2">
                    {p.is_production && <Sparkles size={14} className="text-cyan-400" />}
                    {p.policy_name}
                  </td>
                  <td className="py-3 px-3 font-mono">
                    {p.is_production ? (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-bold">PRODUCTION</span>
                    ) : p.is_experimental ? (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-400 font-bold">EXPERIMENTAL</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-500/20 text-slate-400">BASELINE</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-cyan-300">{p.mean_reward}</td>
                  <td className="py-3 px-3 font-mono text-slate-400">±{p.reward_ci95}</td>
                  <td className="py-3 px-3 font-mono text-slate-300">{p.accuracy_pct}%</td>
                  <td className="py-3 px-3 font-mono text-emerald-400">+{p.net_mastery_gain}</td>
                  <td className="py-3 px-3 font-mono text-slate-400">{p.bkt_mae}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section E: Policy Safety & Invariants */}
      <div className="glass-card p-6 border-emerald-500/20 bg-emerald-500/5 space-y-3">
        <div className="flex items-center gap-2 text-emerald-400 font-bold">
          <Shield size={20} />
          <h3 className="font-display text-base">E. Policy Safety Invariants & Fallback Guarantees</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300 pt-2">
          <div className="p-3 rounded-lg bg-black/20 border border-white/5 space-y-1">
            <span className="font-bold text-white block">1. Action Masking</span>
            <p className="text-slate-400">
              Exercises whose prerequisites have not reached P(L) ≥ 0.70 are strictly masked from policy sampling, preventing cognitive overload.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-black/20 border border-white/5 space-y-1">
            <span className="font-bold text-white block">2. Difficulty Hysteresis</span>
            <p className="text-slate-400">
              Two consecutive errors automatically trigger remedial intervention downshifts, breaking frustrating failure loops.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-black/20 border border-white/5 space-y-1">
            <span className="font-bold text-white block">3. Shadow Gating</span>
            <p className="text-slate-400">
              Experimental deep RL policies run purely in passive shadow evaluation without overriding validated pedagogical exercise delivery.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
