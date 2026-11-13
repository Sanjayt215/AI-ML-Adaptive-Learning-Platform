import React, { useState, useEffect } from 'react';
import { RotateCcw, AlertTriangle, CheckCircle, Clock, Zap, ArrowRight, RefreshCw, BookOpen } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function RevisionSection({ onSelectPractice }) {
  const [revisionPlan, setRevisionPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchPlan = async () => {
    setLoading(true);
    setError('');
    try {
      const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';
      const data = await apiFetch(`/api/revision/plan?learner_id=${learnerId}`);
      if (data && data.ok) {
        setRevisionPlan(data);
      } else {
        throw new Error(data?.error || 'Unable to load revision plan.');
      }
    } catch (err) {
      setError(err.message || 'Error communicating with spaced repetition service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  const summary = revisionPlan?.summary || {
    total_practiced_kcs: 0,
    due_count: 0,
    retained_count: 0,
    avg_retrievability: 1.0,
    avg_retrievability_pct: 100,
  };

  const dueItems = revisionPlan?.due_today || [];
  const upcomingItems = revisionPlan?.upcoming || [];

  return (
    <div className="space-y-6">
      {/* Header & SRS Metric Summary */}
      <div className="glass-card p-6 border-cyan-400/30">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
          <div className="flex items-center gap-2.5">
            <RotateCcw className="text-cyan-400" size={20} />
            <div>
              <h3 className="font-display font-semibold text-white text-base">Spaced Repetition System (SRS) Revision Plan</h3>
              <p className="text-slate-400 text-xs">
                Half-Life Memory Decay model: <span className="font-mono text-cyan-400">R(t) = 2^(-Δt / S)</span> · Items due when recall drops below 85%
              </p>
            </div>
          </div>
          <button
            onClick={fetchPlan}
            disabled={loading}
            className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh Queue
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Due for Review</span>
            <span className="font-mono text-lg font-bold text-red-400">{summary.due_count}</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Urgent memory recovery</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Retained Concepts</span>
            <span className="font-mono text-lg font-bold text-green-400">{summary.retained_count}</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Recall strength &gt; 85%</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Avg Retrievability</span>
            <span className="font-mono text-lg font-bold text-cyan-400">{summary.avg_retrievability_pct}%</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Across active KCs</span>
          </div>
          <div className="glass-card p-3">
            <span className="text-slate-500 block mb-1">Total KCs in SRS</span>
            <span className="font-mono text-lg font-bold text-purple-400">{summary.total_practiced_kcs}</span>
            <span className="text-slate-400 block text-[10px] mt-0.5">Practiced topics</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-purple-400/10 border border-purple-400/20 text-xs text-slate-300 leading-relaxed">
          <span className="text-purple-300 font-semibold">SRS Mechanics: </span>
          Each correct recall doubles stability (<span className="font-mono text-white">S_{'{n+1}'} = S_n * 2.0</span>), extending the spacing interval. 
          Any lapse or incorrect answer resets stability to <span className="font-mono text-white">S = 1.0</span> for prompt reinforcement.
        </div>
      </div>

      {loading && (
        <div className="py-8 text-center text-slate-400 text-sm animate-pulse">
          Computing longitudinal memory stability and retrieval strength across knowledge components...
        </div>
      )}

      {error && !loading && (
        <div className="p-4 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300 text-xs">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Due Today Queue */}
          <div className="glass-card p-6 border-red-400/25 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-red-400" />
                <h4 className="font-display font-semibold text-white text-sm">Due for Review Today</h4>
              </div>
              <span className="badge-chip border border-red-400/30 text-red-400 bg-red-400/10 text-xs">
                {dueItems.length} Due
              </span>
            </div>

            {dueItems.length === 0 ? (
              <div className="p-6 rounded-xl bg-white/4 border border-white/8 text-center space-y-2">
                <CheckCircle size={28} className="text-green-400 mx-auto opacity-80" />
                <div className="font-display font-medium text-white text-sm">Zero Items Due</div>
                <p className="text-slate-400 text-xs">
                  {summary.total_practiced_kcs === 0
                    ? 'No practice events recorded yet. Complete quiz items to populate your spaced repetition schedule.'
                    : 'All practiced concepts are currently retained above the 85% retrievability threshold!'}
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {dueItems.map(item => (
                  <div
                    key={item.kc_id}
                    className="p-3.5 rounded-xl bg-red-400/5 border border-red-400/20 flex items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="font-display font-semibold text-white text-sm capitalize">
                        {item.topic.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span>Recall: <strong className="font-mono text-red-400">{item.retrievability_pct}%</strong></span>
                        <span>·</span>
                        <span>Stability: <strong className="font-mono text-white">{item.stability}x</strong></span>
                        <span>·</span>
                        <span>Lapsed {item.elapsed_steps} steps ago</span>
                      </div>
                    </div>
                    {onSelectPractice && (
                      <button
                        onClick={() => onSelectPractice(item.topic)}
                        className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1 flex-shrink-0"
                      >
                        Review Now <ArrowRight size={12} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming Retained Queue */}
          <div className="glass-card p-6 border-white/10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-green-400" />
                <h4 className="font-display font-semibold text-white text-sm">Retained & Upcoming Reviews</h4>
              </div>
              <span className="badge-chip border border-green-400/30 text-green-400 bg-green-400/10 text-xs">
                {upcomingItems.length} Retained
              </span>
            </div>

            {upcomingItems.length === 0 ? (
              <div className="p-6 rounded-xl bg-white/4 border border-white/8 text-center space-y-2">
                <Clock size={28} className="text-slate-500 mx-auto opacity-80" />
                <div className="font-display font-medium text-white text-sm">No Upcoming Reviews</div>
                <p className="text-slate-400 text-xs">
                  Concepts will appear here as you practice and expand their memory half-life.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {upcomingItems.map(item => (
                  <div
                    key={item.kc_id}
                    className="p-3.5 rounded-xl bg-white/4 border border-white/8 flex items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="font-display font-semibold text-white text-sm capitalize">
                        {item.topic.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span>Recall: <strong className="font-mono text-green-400">{item.retrievability_pct}%</strong></span>
                        <span>·</span>
                        <span>Stability: <strong className="font-mono text-cyan-400">{item.stability}x</strong></span>
                        <span>·</span>
                        <span>{item.repetition_count} successful reviews</span>
                      </div>
                    </div>
                    <span className="badge-chip text-[10px] text-green-400 bg-green-400/10 border border-green-400/20">
                      Retained
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
