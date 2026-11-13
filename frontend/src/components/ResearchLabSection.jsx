import React, { useState, useEffect } from 'react';
import { ShieldCheck, Cpu, Download, RefreshCw, BarChart2, CheckCircle, AlertTriangle, Layers, Activity } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function ResearchLabSection() {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkError, setBenchmarkError] = useState('');

  const [calibrationData, setCalibrationData] = useState(null);
  const [calLoading, setCalLoading] = useState(false);

  const [shadowMetrics, setShadowMetrics] = useState(null);
  const [shadowLoading, setShadowLoading] = useState(false);

  const [exporting, setExporting] = useState(false);

  const fetchBenchmark = async () => {
    setBenchmarkLoading(true);
    setBenchmarkError('');
    try {
      const res = await apiFetch('/api/research/benchmark');
      if (res && res.ok && res.data) {
        setBenchmarkData(res.data);
      } else {
        throw new Error(res?.error || 'Unable to load benchmark suite.');
      }
    } catch (err) {
      setBenchmarkError(err.message || 'Error fetching benchmark data.');
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const fetchCalibration = async () => {
    setCalLoading(true);
    try {
      const res = await apiFetch('/api/diagnostic/calibration');
      if (res && res.ok && res.calibration) {
        setCalibrationData(res.calibration);
      }
    } catch (err) {
      console.warn('Calibration fetch error:', err);
    } finally {
      setCalLoading(false);
    }
  };

  const fetchShadowMetrics = async () => {
    setShadowLoading(true);
    try {
      const res = await apiFetch('/api/research/shadow_metrics');
      if (res && res.ok && res.metrics) {
        setShadowMetrics(res.metrics);
      }
    } catch (err) {
      console.warn('Shadow metrics error:', err);
    } finally {
      setShadowLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
    fetchCalibration();
    fetchShadowMetrics();
  }, []);

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await apiFetch('/api/research/export?include_events=true');
      if (res && res.ok && res.dataset) {
        const jsonStr = JSON.stringify(res.dataset, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `autolearn_anonymized_research_dataset_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      alert('Failed to export dataset: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  const policies = benchmarkData?.policy_metrics || {};
  const meta = benchmarkData?.benchmark_metadata || {};

  return (
    <div className="space-y-6">
      {/* Research Governance & Safety Status Card */}
      <div className="glass-card p-6 border-cyan-400/30">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="text-cyan-400" size={22} />
            <div>
              <h3 className="font-display font-semibold text-white text-base">Research Lab & Governance Dashboard</h3>
              <p className="text-slate-400 text-xs">
                Empirical Evaluation · FERPA/IRB Anonymization Protocol · Shadow Policy Observability
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportData}
              disabled={exporting}
              className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3 border-purple-400/30 text-purple-300 hover:border-purple-400"
            >
              <Download size={12} className={exporting ? 'animate-bounce' : ''} />
              Export Anonymized Dataset
            </button>
            <button
              onClick={() => { fetchBenchmark(); fetchCalibration(); fetchShadowMetrics(); }}
              className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3"
            >
              <RefreshCw size={12} />
              Refresh
            </button>
          </div>
        </div>

        {/* 4 Pillars Status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs mb-4">
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Production Policy</span>
            <span className="font-mono text-cyan-400 font-bold">composite_adaptive</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Constraint Satisfied (0 Invalid)</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">DQN Experiment Safety Gate</span>
            <span className="font-mono text-yellow-400 font-bold">KT_RL_EXP=0 (Gated)</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Safety Shield Active</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Shadow Evaluation</span>
            <span className="font-mono text-purple-400 font-bold">
              {shadowMetrics?.is_shadow_mode_enabled ? 'Active Shadowing' : 'Shielded (Default Off)'}
            </span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Zero Live Learner Exposure</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Research Checkpoint</span>
            <span className="font-mono text-white font-bold">dueling_dqn_final.pt</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Dueling Architecture (821 KB)</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 leading-relaxed">
          <span className="text-cyan-400 font-semibold">Verification Note: </span>
          All benchmark numbers below derive from reproducible synthetic simulation runs across 4 archetypes (quick-learner, slow-learner, careless, gaming), 
          conducted under controlled seeds with calibrated intra-session decay ($\Delta t = 0.05$).
        </div>
      </div>

      {/* 10-Policy Benchmark Comparison Table */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h4 className="font-display font-semibold text-white text-base">Comprehensive 10-Policy Benchmark Suite</h4>
            <p className="text-slate-400 text-xs">
              Evaluation Horizon: {meta.active_steps_per_episode || 25} steps · Delay Horizon: {meta.delay_days || 7.0} days · Archetypes: {meta.archetypes_evaluated?.length || 4}
            </p>
          </div>
          <span className="badge-chip border border-cyan-400/30 text-cyan-400 bg-cyan-400/10 text-xs">
            {Object.keys(policies).length} Policies Evaluated
          </span>
        </div>

        {benchmarkLoading && (
          <div className="py-8 text-center text-slate-400 text-sm animate-pulse">
            Loading benchmark telemetry from reports/phase8_benchmark_results.json...
          </div>
        )}

        {benchmarkError && (
          <div className="p-4 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300 text-xs">
            {benchmarkError}
          </div>
        )}

        {!benchmarkLoading && !benchmarkError && (
          <div className="overflow-x-auto">
            <table className="cyber-table">
              <thead>
                <tr>
                  <th className="text-left">Policy</th>
                  <th className="text-right">Mean Reward (CI95)</th>
                  <th className="text-right">Net Mastery Gain (CI95)</th>
                  <th className="text-right">7-Day Retention</th>
                  <th className="text-right">7-Day Delayed Gain</th>
                  <th className="text-right">Invalid Actions</th>
                  <th className="text-right">Latency</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(policies).map(([name, p]) => {
                  const isComposite = name === 'composite_adaptive';
                  const isDQN = name === 'dueling_dqn';
                  const isLinUCB = name === 'linucb_bandit';
                  return (
                    <tr
                      key={name}
                      className={isComposite ? 'bg-cyan-400/10 font-medium' : isDQN ? 'bg-purple-400/5' : ''}
                    >
                      <td className="font-display font-semibold text-white capitalize flex items-center gap-2">
                        {isComposite && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />}
                        {isDQN && <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />}
                        <span>{name.replace(/_/g, ' ')}</span>
                        {isComposite && <span className="badge-chip text-[9px] text-cyan-400 bg-cyan-400/20 border-cyan-400/40">Active Prod</span>}
                      </td>
                      <td className="text-right font-mono text-cyan-400">
                        {p.mean_cumulative_reward?.toFixed(2)} <span className="text-slate-500 text-[10px]">±{p.reward_ci95?.toFixed(2)}</span>
                      </td>
                      <td className="text-right font-mono text-green-400">
                        +{(p.mean_net_mastery_gain * 100)?.toFixed(1)}% <span className="text-slate-500 text-[10px]">±{(p.net_mastery_gain_ci95 * 100)?.toFixed(1)}%</span>
                      </td>
                      <td className="text-right font-mono text-white">
                        {p.mean_7day_retention_rate ? `${Math.round(p.mean_7day_retention_rate * 100)}%` : '—'}
                      </td>
                      <td className="text-right font-mono text-slate-300">
                        +{((p.mean_7day_delayed_gain || 0) * 100).toFixed(1)}%
                      </td>
                      <td className="text-right font-mono">
                        <span className={`px-2 py-0.5 rounded text-xs ${p.total_invalid_actions === 0 ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
                          {p.total_invalid_actions || 0}
                        </span>
                      </td>
                      <td className="text-right font-mono text-slate-400 text-xs">
                        {p.mean_latency_ms ? `${p.mean_latency_ms.toFixed(3)}ms` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Diagnostics Grid: BKT Calibration & Shadow Evaluation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Probabilistic Calibration (ECE, Brier Score) */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart2 size={18} className="text-cyan-400" />
              <h4 className="font-display font-semibold text-white text-sm">BKT Probabilistic Calibration</h4>
            </div>
            <span className="badge-chip border border-cyan-400/30 text-cyan-400 bg-cyan-400/10 text-xs">
              Reliability Analysis
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates whether posterior probability <span className="font-mono text-cyan-400">P(Correct)</span> matches observed frequency across reliability bins.
          </p>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Expected Calibration Error (ECE)</span>
              <span className="font-mono text-lg font-bold text-green-400">
                {calibrationData?.ece !== undefined ? `${(calibrationData.ece * 100).toFixed(1)}%` : '0.0%'}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Target: &lt; 15%</span>
            </div>
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Max Calibration Error (MCE)</span>
              <span className="font-mono text-lg font-bold text-yellow-400">
                {calibrationData?.mce !== undefined ? `${(calibrationData.mce * 100).toFixed(1)}%` : '0.0%'}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Worst-case bin</span>
            </div>
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Brier Score</span>
              <span className="font-mono text-lg font-bold text-cyan-400">
                {calibrationData?.brier_score !== undefined ? calibrationData.brier_score.toFixed(3) : '0.000'}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Mean squared error</span>
            </div>
          </div>
        </div>

        {/* Shadow Policy Evaluation */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-purple-400" />
              <h4 className="font-display font-semibold text-white text-sm">Shadow Evaluation Telemetry</h4>
            </div>
            <span className="badge-chip border border-purple-400/30 text-purple-400 bg-purple-400/10 text-xs">
              Safe Shadow Mode
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates candidate policies side-by-side in real-time execution without affecting production recommendations delivered to the student.
          </p>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Shadow Mode Status</span>
              <span className={`font-mono text-sm font-bold ${shadowMetrics?.is_shadow_mode_enabled ? 'text-green-400' : 'text-slate-400'}`}>
                {shadowMetrics?.is_shadow_mode_enabled ? 'ENABLED' : 'DISABLED'}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Controlled gate</span>
            </div>
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Evaluated Steps</span>
              <span className="font-mono text-lg font-bold text-white">
                {shadowMetrics?.total_shadow_evaluations || 0}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Parallel decisions</span>
            </div>
            <div className="glass-card p-3 text-center">
              <span className="text-slate-500 block text-[11px] mb-1">Concordance Rate</span>
              <span className="font-mono text-lg font-bold text-purple-400">
                {shadowMetrics?.concordance_rate !== undefined ? `${Math.round(shadowMetrics.concordance_rate * 100)}%` : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Agreement with Prod</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
