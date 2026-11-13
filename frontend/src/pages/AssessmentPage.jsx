import React, { useState, useEffect } from 'react';
import { Award, RefreshCcw, CheckCircle2, ArrowRight, Brain } from 'lucide-react';
import AssessmentModal from '../components/AssessmentModal';
import { apiFetch } from '../utils/api';

export default function AssessmentPage() {
  const [isOpen, setIsOpen] = useState(true);
  const [learnerId] = useState(() => {
    return localStorage.getItem('autolearn_learner_id') || 'learner_default';
  });
  const [comparison, setComparison] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAssessmentData = async () => {
    setLoading(true);
    try {
      const [compRes, histRes] = await Promise.all([
        apiFetch(`/api/assessment/compare/${learnerId}`).catch(() => null),
        apiFetch(`/api/assessment/history/${learnerId}`).catch(() => null),
      ]);
      if (compRes && compRes.ok) setComparison(compRes.comparison);
      if (histRes && histRes.ok) setHistory(histRes.history || []);
    } catch (e) {
      console.warn('Error loading assessment history:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessmentData();
  }, [learnerId]);

  return (
    <div className="px-6 py-8 max-w-4xl mx-auto space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-400 text-xs font-mono mb-2">
              DIAGNOSTIC BENCHMARK
            </div>
            <h1 className="font-display font-bold text-2xl text-white">Diagnostic Pre/Post Assessment</h1>
            <p className="text-slate-400 text-sm mt-1">
              Independent, unassisted test evaluation to objectively benchmark student knowledge growth and Hake's normalized gain.
            </p>
          </div>
          <button
            onClick={() => setIsOpen(true)}
            className="btn-cyber-solid flex items-center gap-2 text-xs py-2 px-4"
          >
            <Award size={16} /> Take Assessment
          </button>
        </div>

        {/* Comparison card if pre + post exist */}
        {comparison && comparison.has_both ? (
          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-3">
            <h3 className="font-display font-semibold text-white text-sm">Learning Gain Summary</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-2.5 rounded-lg bg-black/30">
                <div className="text-slate-400 text-[10px]">Pre-Score</div>
                <div className="font-mono text-cyan-300 font-bold text-lg">{comparison.pre_score_pct}%</div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30">
                <div className="text-slate-400 text-[10px]">Post-Score</div>
                <div className="font-mono text-green-300 font-bold text-lg">{comparison.post_score_pct}%</div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30">
                <div className="text-slate-400 text-[10px]">Absolute Gain</div>
                <div className="font-mono text-white font-bold text-lg">+{comparison.absolute_gain_pct}%</div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30">
                <div className="text-slate-400 text-[10px]">Hake's Gain (g)</div>
                <div className="font-mono text-purple-300 font-bold text-lg">{comparison.normalized_gain_hake}</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300">
            Take a <strong>Pre-Assessment</strong> before your study modules and a <strong>Post-Assessment</strong> after completion to scientifically compute your learning gain.
          </div>
        )}
      </div>

      {/* Assessment History Table */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display font-semibold text-white text-base">Completed Assessment Sessions</h2>
          <button onClick={fetchAssessmentData} disabled={loading} className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3">
            <RefreshCcw size={12} /> Refresh
          </button>
        </div>

        {history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-slate-300 border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-slate-500 font-semibold text-left">
                  <th className="py-2 px-3">Type</th>
                  <th className="py-2 px-3">Date</th>
                  <th className="py-2 px-3">Questions</th>
                  <th className="py-2 px-3">Score</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                    <td className="py-2.5 px-3 uppercase font-mono font-bold text-cyan-400">{h.assessment_type}</td>
                    <td className="py-2.5 px-3">{h.started_at ? new Date(h.started_at).toLocaleDateString() : 'Recent'}</td>
                    <td className="py-2.5 px-3 font-mono">{h.total_questions || h.num_questions} items</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-white">
                      {h.score_pct != null ? `${h.score_pct}% (${h.score}/${h.total_questions || h.num_questions})` : (h.accuracy != null ? `${Math.round(h.accuracy * 100)}% (${h.score}/${h.total_questions || h.num_questions})` : (h.score != null ? `${h.score} pts` : '--'))}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="badge-chip text-[10px] text-green-400 bg-green-400/10">Completed</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500 text-xs">
            No completed assessments recorded yet. Click "Take Assessment" above to begin.
          </div>
        )}
      </div>

      {/* Assessment Modal */}
      {isOpen && (
        <AssessmentModal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onComplete={() => {
            fetchAssessmentData();
          }}
        />
      )}
    </div>
  );
}
