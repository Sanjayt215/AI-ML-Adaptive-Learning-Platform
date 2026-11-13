import React from 'react';
import { X, Brain, CheckCircle2, AlertTriangle, Layers, ArrowRight, ShieldCheck } from 'lucide-react';

export default function KCDetailModal({ kc, onClose, onPractice }) {
  if (!kc) return null;

  const isAssessed = kc.status === 'assessed' || (kc.observation_count && kc.observation_count > 0);
  const pct = kc.mastery_pct ?? Math.round((kc.mastery_probability || kc.current_mastery || 0) * 100);
  const color = !isAssessed ? '#94a3b8' : pct >= 75 ? '#4ade80' : pct >= 50 ? '#fbbf24' : '#f87171';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-card max-w-lg w-full p-6 border-cyan-400/30 relative space-y-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain size={18} className="text-cyan-400" />
              <h3 className="font-display font-bold text-lg text-white capitalize">
                {kc.kc_id ? kc.kc_id.replace(/_/g, ' ') : kc.topic ? kc.topic.replace(/_/g, ' ') : 'Concept Detail'}
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              KC Identifier: <span className="text-cyan-400">{kc.kc_id || kc.topic}</span>
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Estimated Mastery Overview */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-300 font-medium">BKT Estimated Mastery P(K)</span>
            <span className="font-mono text-sm font-bold" style={{ color }}>
              {isAssessed ? `${pct}%` : 'Unassessed'}
            </span>
          </div>
          <div className="difficulty-track w-full h-2">
            <div
              className="difficulty-fill h-full"
              style={{ width: `${isAssessed ? pct : 20}%`, background: color }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Prior P(L₀): 20%</span>
            <span>Mastery Threshold: 80%</span>
          </div>
        </div>

        {/* Observation Evidence */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Evidence Status</span>
            <span className={`badge-chip text-[11px] capitalize ${isAssessed ? 'text-green-400 bg-green-400/10' : 'text-slate-400 bg-white/5'}`}>
              {isAssessed ? (kc.evidence_quality || 'Assessed') : 'Not yet assessed'}
            </span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Practice Observations</span>
            <span className="font-mono text-white text-xs font-semibold">
              {isAssessed ? (
                <span>
                  <span className="text-green-400">{kc.correct_count || 0}C</span> / <span className="text-red-400">{kc.incorrect_count || 0}I</span> ({kc.observation_count || 0} total)
                </span>
              ) : (
                '0 responses recorded'
              )}
            </span>
          </div>
        </div>

        {/* BKT Model Parameters */}
        <div className="p-3.5 rounded-xl bg-purple-400/10 border border-purple-400/20 text-xs space-y-2">
          <div className="flex items-center gap-1.5 text-purple-300 font-semibold">
            <ShieldCheck size={14} /> Latent BKT Parameter Profile:
          </div>
          <div className="grid grid-cols-4 gap-2 font-mono text-[11px] text-center">
            <div className="bg-black/30 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">P(L₀)</span>
              <span className="text-slate-200">0.20</span>
            </div>
            <div className="bg-black/30 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">P(T)</span>
              <span className="text-slate-200">0.15</span>
            </div>
            <div className="bg-black/30 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">P(G)</span>
              <span className="text-slate-200">0.20</span>
            </div>
            <div className="bg-black/30 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">P(S)</span>
              <span className="text-slate-200">0.10</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            Estimated sequentially using Bayesian updating: P(K|evidence) accounts for slip and guess probabilities.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition"
          >
            Close
          </button>
          {onPractice && (
            <button
              onClick={() => {
                onClose();
                onPractice(kc.kc_id || kc.topic);
              }}
              className="btn-cyber text-xs flex items-center gap-1.5 py-2 px-4"
            >
              Practice This Concept <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
