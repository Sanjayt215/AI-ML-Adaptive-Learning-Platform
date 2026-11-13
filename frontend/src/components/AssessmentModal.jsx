import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, AlertCircle, Clock, Award, ArrowRight, RefreshCw, BarChart2, ShieldAlert } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function AssessmentModal({ isOpen, onClose, onComplete }) {
  const [stage, setStage] = useState('config'); // 'config' | 'taking' | 'submitting' | 'results'
  const [assessmentType, setAssessmentType] = useState('pre');
  const [numQuestions, setNumQuestions] = useState(5);
  const [sessionData, setSessionData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState({});
  const [responseTimes, setResponseTimes] = useState({});
  const [qStartTime, setQStartTime] = useState(Date.now());
  const [totalTimer, setTotalTimer] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submissionResults, setSubmissionResults] = useState(null);
  const [comparison, setComparison] = useState(null);

  const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';

  // Timer effect
  useEffect(() => {
    let interval = null;
    if (stage === 'taking') {
      interval = setInterval(() => {
        setTotalTimer(t => t + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [stage]);

  // Record presentation start time for each question
  useEffect(() => {
    setQStartTime(Date.now());
  }, [currentIndex, stage]);

  if (!isOpen) return null;

  const startAssessment = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch('/api/assessment/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          assessment_type: assessmentType,
          num_questions: numQuestions,
        }),
      });

      if (data && data.ok && data.assessment) {
        setSessionData(data.assessment);
        setResponses({});
        setResponseTimes({});
        setCurrentIndex(0);
        setTotalTimer(0);
        setStage('taking');
      } else {
        throw new Error(data?.error || 'Failed to start assessment session.');
      }
    } catch (err) {
      setError(err.message || 'Error communicating with assessment service.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (opt) => {
    const elapsed = Date.now() - qStartTime;
    const currentQ = sessionData?.questions?.[currentIndex];
    if (!currentQ) return;

    setResponses(prev => ({
      ...prev,
      [currentQ.item_id]: opt,
    }));

    setResponseTimes(prev => ({
      ...prev,
      [currentQ.item_id]: (prev[currentQ.item_id] || 0) + Math.max(elapsed, 100),
    }));
    setQStartTime(Date.now());
  };

  const submitAssessment = async () => {
    setStage('submitting');
    setError('');
    try {
      const formattedResponses = (sessionData?.questions || []).map(q => ({
        item_id: q.item_id,
        selected_option: responses[q.item_id] || '',
        response_time_ms: responseTimes[q.item_id] || 1000,
      }));

      const res = await apiFetch('/api/assessment/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assessment_id: sessionData.assessment_id,
          responses: formattedResponses,
        }),
      });

      if (res && res.ok && res.results) {
        setSubmissionResults(res.results);

        // Fetch pre-post comparison
        try {
          const compData = await apiFetch(`/api/assessment/compare/${learnerId}`);
          if (compData && compData.ok) {
            setComparison(compData.comparison);
          }
        } catch {
          // ignore comparison fetch error if only pre assessment exists
        }

        setStage('results');
        if (onComplete) onComplete();
      } else {
        throw new Error(res?.error || 'Failed to score assessment.');
      }
    } catch (err) {
      setError(err.message || 'Submission error.');
      setStage('taking');
    }
  };

  const questions = sessionData?.questions || [];
  const currentQ = questions[currentIndex];
  const allAnswered = questions.length > 0 && questions.every(q => responses[q.item_id]);

  const formatSeconds = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="glass-card max-w-2xl w-full p-6 border-cyan-400/40 relative space-y-6 shadow-2xl my-8">

        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2.5">
            <Award className="text-cyan-400" size={22} />
            <div>
              <h3 className="font-display font-bold text-lg text-white">
                {stage === 'config' && 'Diagnostic Assessment Setup'}
                {stage === 'taking' && `${assessmentType.toUpperCase()}-Assessment in Progress`}
                {stage === 'results' && 'Diagnostic Assessment Results'}
              </h3>
              <p className="text-slate-400 text-xs">
                {stage === 'config' && 'Independent empirical measurement without instructional scaffolding'}
                {stage === 'taking' && `Question ${currentIndex + 1} of ${questions.length} · Answers concealed until submission`}
                {stage === 'results' && 'Direct observable test score evaluation'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-400/10 border border-red-400/25 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ── STAGE 1: CONFIG ── */}
        {stage === 'config' && (
          <div className="space-y-5">
            <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 leading-relaxed">
              <span className="text-cyan-400 font-semibold">Evaluation Protocol Notice: </span>
              Assessments evaluate factual knowledge components directly. Unlike adaptive practice, answers and feedback are concealed until all items are completed to preserve measurement validity.
            </div>

            <div className="space-y-3">
              <label className="text-sm font-display font-semibold text-white block">Assessment Type</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setAssessmentType('pre')}
                  className={`p-3.5 rounded-xl border text-left transition ${
                    assessmentType === 'pre'
                      ? 'bg-cyan-400/15 border-cyan-400/50 text-white'
                      : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                  }`}
                >
                  <div className="font-bold text-sm text-cyan-400 mb-0.5">Pre-Assessment</div>
                  <div className="text-xs text-slate-400">Baseline diagnostic before adaptive exercises</div>
                </button>
                <button
                  type="button"
                  onClick={() => setAssessmentType('post')}
                  className={`p-3.5 rounded-xl border text-left transition ${
                    assessmentType === 'post'
                      ? 'bg-purple-400/15 border-purple-400/50 text-white'
                      : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                  }`}
                >
                  <div className="font-bold text-sm text-purple-400 mb-0.5">Post-Assessment</div>
                  <div className="text-xs text-slate-400">Evaluate learning gain & Hake's normalized gain</div>
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-display font-semibold text-white block">Number of Questions</label>
              <div className="flex gap-3">
                {[5, 10].map(count => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setNumQuestions(count)}
                    className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition border ${
                      numQuestions === count
                        ? 'bg-cyan-400 text-dark-300 border-cyan-400'
                        : 'bg-white/5 text-slate-300 border-white/10 hover:border-white/20'
                    }`}
                  >
                    {count} Questions
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-4 flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={startAssessment}
                disabled={loading}
                className="btn-cyber text-xs flex items-center gap-2 py-2.5 px-5"
              >
                {loading ? <RefreshCw size={14} className="animate-spin" /> : null}
                Start Assessment <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ── STAGE 2: TAKING ASSESSMENT ── */}
        {stage === 'taking' && currentQ && (
          <div className="space-y-5">
            {/* Top status bar */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 font-mono text-cyan-400">
                <Clock size={14} />
                <span>Elapsed: {formatSeconds(totalTimer)}</span>
              </div>
              <div className="text-slate-400">
                Answered <span className="text-white font-mono">{Object.keys(responses).length}</span> / {questions.length}
              </div>
            </div>

            {/* Progress bar */}
            <div className="difficulty-track w-full h-1.5">
              <div
                className="difficulty-fill h-full bg-cyan-400"
                style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
              />
            </div>

            {/* Question Card */}
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="badge-chip border border-cyan-400/30 text-cyan-400 bg-cyan-400/10 text-xs capitalize">
                  {currentQ.topic ? currentQ.topic.replace(/_/g, ' ') : 'Topic'}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Item #{currentIndex + 1} · Diff {currentQ.difficulty}/5
                </span>
              </div>

              <p className="text-base text-slate-100 font-medium leading-relaxed">
                {currentQ.question}
              </p>

              {/* Options */}
              <div className="space-y-2.5 pt-2">
                {(currentQ.options || []).map((opt, i) => {
                  const isSelected = responses[currentQ.item_id] === opt;
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSelectOption(opt)}
                      className={`w-full p-3.5 rounded-xl border text-left text-sm transition flex items-center justify-between ${
                        isSelected
                          ? 'bg-cyan-400/20 border-cyan-400 text-white font-medium'
                          : 'bg-white/4 border-white/8 text-slate-300 hover:bg-white/8 hover:border-white/20'
                      }`}
                    >
                      <span>{opt}</span>
                      {isSelected && <CheckCircle2 size={16} className="text-cyan-400 flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Navigation buttons */}
            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => setCurrentIndex(i => Math.max(0, i - 1))}
                disabled={currentIndex === 0}
                className="btn-cyber text-xs py-2 px-3 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <div className="flex items-center gap-2">
                {currentIndex < questions.length - 1 ? (
                  <button
                    type="button"
                    onClick={() => setCurrentIndex(i => Math.min(questions.length - 1, i + 1))}
                    className="btn-cyber text-xs py-2 px-4"
                  >
                    Next Question
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={submitAssessment}
                    disabled={!allAnswered}
                    className="btn-cyber text-xs py-2 px-5 bg-cyan-400 text-dark-300 font-bold border-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Submit Assessment
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── STAGE 3: RESULTS ── */}
        {stage === 'results' && submissionResults && (
          <div className="space-y-5">
            {/* Score banner */}
            <div className="p-5 rounded-2xl bg-gradient-to-r from-cyan-400/10 via-purple-400/10 to-transparent border border-cyan-400/30 flex items-center justify-between flex-wrap gap-4">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-cyan-400 block mb-1">
                  {submissionResults.assessment_type?.toUpperCase()} Assessment Completed
                </span>
                <div className="text-3xl font-display font-bold text-white">
                  {Math.round((submissionResults.score || 0) * 100)}%
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Correct: <span className="text-green-400 font-bold">{submissionResults.correct_count}</span> / {submissionResults.total_questions}
                </p>
              </div>

              {/* Hake's Gain if comparison available */}
              {comparison && comparison.has_both && (
                <div className="glass-card p-3.5 border-purple-400/30 text-right">
                  <span className="text-[11px] text-purple-300 font-medium block">Hake's Normalized Gain (g)</span>
                  <span className="text-2xl font-mono font-bold text-purple-400">
                    {comparison.hake_normalized_gain !== null ? `${Math.round(comparison.hake_normalized_gain * 100)}%` : '—'}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Pre: {Math.round(comparison.pre_score * 100)}% → Post: {Math.round(comparison.post_score * 100)}%
                  </span>
                </div>
              )}
            </div>

            {/* Distinction Alert */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5">
              <ShieldAlert size={16} className="text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-purple-300 font-semibold">Evaluation Hierarchy Distinction: </span>
                This score reflects direct unassisted test responses. In contrast, BKT values are latent probabilistic estimates updated sequentially over time.
              </div>
            </div>

            {/* Per-Question Breakdown */}
            <div className="space-y-2">
              <h4 className="font-display font-semibold text-white text-sm">Question Feedback</h4>
              <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                {(submissionResults.per_item_results || []).map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-xs space-y-1 ${
                      item.is_correct
                        ? 'bg-green-400/5 border-green-400/20'
                        : 'bg-red-400/5 border-red-400/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold capitalize text-white">
                        {item.topic ? item.topic.replace(/_/g, ' ') : `Question ${idx + 1}`}
                      </span>
                      <span className={`badge-chip text-[10px] font-bold ${item.is_correct ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
                        {item.is_correct ? 'Correct' : 'Incorrect'}
                      </span>
                    </div>
                    <div className="text-slate-300 text-[11px]">
                      Your answer: <span className={item.is_correct ? 'text-green-400' : 'text-red-400'}>{item.selected_option || 'None'}</span>
                    </div>
                    {!item.is_correct && item.correct_option && (
                      <div className="text-slate-400 text-[11px]">
                        Correct answer: <span className="text-cyan-400">{item.correct_option}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Close button */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={onClose}
                className="btn-cyber text-xs py-2 px-5"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
