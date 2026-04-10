
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ChevronLeft, ChevronRight, CheckCircle, Clock, AlertCircle, RefreshCcw } from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import { apiFetch } from '../utils/api';

export default function QuizPage() {
  const navigate = useNavigate();
  const { quizItems, savePartial, refresh } = useFlaskData();
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadQuiz = async (forceNew = false) => {
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch(`/api/quiz${forceNew ? '?refresh=1' : ''}`);
      savePartial({ quizItems: data.quizItems });
      setAnswers({});
      setCurrentQ(0);
    } catch (err) {
      setError(err.message || 'Unable to load quiz.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!quizItems?.length) loadQuiz(false);
  }, []);

  const total = quizItems?.length || 0;
  const progress = total ? (Object.keys(answers).length / total) * 100 : 0;
  const item = quizItems?.[currentQ];
  const key = item ? `${item.topic}_${item.index}` : '';

  const difficultyConfig = {
    beginner: { label: 'Beginner', color: '#4ade80', pct: 30 },
    intermediate: { label: 'Intermediate', color: '#fbbf24', pct: 60 },
    advanced: { label: 'Advanced', color: '#f87171', pct: 90 },
  };

  const answeredAll = total > 0 && Object.keys(answers).length === total;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answeredAll) return;
    setSubmitted(true);
    setError('');
    try {
      const data = await apiFetch('/api/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      });
      savePartial(data);
      await refresh();
      navigate('/dashboard');
    } catch (err) {
      setSubmitted(false);
      setError(err.message || 'Quiz submission failed.');
    }
  };

  if (loading && !total) {
    return <div className="px-6 py-8 max-w-2xl mx-auto text-slate-300">Loading quiz...</div>;
  }

  if (!total) {
    return (
      <div className="px-6 py-8 max-w-2xl mx-auto">
        <div className="glass-card p-8 text-center space-y-4">
          <div className="text-white text-lg font-display">No quiz generated yet</div>
          <div className="text-slate-500 text-sm">Start with your syllabus first.</div>
          {error && <div className="text-red-400 text-sm">{error}</div>}
          <button onClick={() => navigate('/start')} className="btn-cyber-solid">Go to Start</button>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="px-6 py-8 max-w-2xl mx-auto text-center">
        <div className="glass-card p-10">
          <div className="w-20 h-20 rounded-full bg-green-400/10 border border-green-400/30 flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={36} className="text-green-400" />
          </div>
          <h2 className="font-display font-bold text-2xl text-white mb-3">Quiz Submitted!</h2>
          <p className="text-slate-400 mb-6">Opening your personalized dashboard...</p>
        </div>
      </div>
    );
  }

  const diff = difficultyConfig[item?.difficulty || 'beginner'];

  return (
    <div className="px-6 py-8 max-w-3xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-400 text-xs font-mono mb-4">STEP 3 OF 4 · KNOWLEDGE ASSESSMENT</div>
          <h1 className="font-display font-bold text-2xl text-white">Adaptive Knowledge Quiz</h1>
          <p className="text-slate-400 text-sm mt-1">Unique questions are generated from your selected syllabus topics.</p>
        </div>
        <button type="button" onClick={() => loadQuiz(true)} className="btn-cyber flex items-center gap-2">
          <RefreshCcw size={14} /> New Quiz
        </button>
      </div>

      <div className="glass-card p-4 mb-6 flex items-center gap-6">
        <div className="flex-1">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-slate-400">Overall Progress</span>
            <span className="text-cyan-400 font-mono font-medium">{Object.keys(answers).length}/{total}</span>
          </div>
          <div className="difficulty-track"><div className="difficulty-fill bg-gradient-to-r from-cyan-400 to-purple-500" style={{ width: `${progress}%` }} /></div>
        </div>
        <div className="text-center"><div className="font-display font-bold text-white text-2xl">{currentQ + 1}</div><div className="text-slate-500 text-xs">of {total}</div></div>
        <div className="flex items-center gap-1.5 text-slate-400 text-xs"><Clock size={12} /><span>~{Math.ceil(total * 1.5)} min</span></div>
      </div>

      <form onSubmit={handleSubmit}>
        {quizItems.map((q, idx) => {
          const qKey = `${q.topic}_${q.index}`;
          return (
            <div key={qKey} style={{ display: idx === currentQ ? 'block' : 'none' }}>
              <div className="glass-card p-6 mb-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="px-3 py-1 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 text-xs font-semibold font-mono uppercase tracking-wider">{q.topic}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Difficulty</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-20 difficulty-track"><div className="difficulty-fill" style={{ width: `${difficultyConfig[q.difficulty || 'beginner'].pct}%`, background: difficultyConfig[q.difficulty || 'beginner'].color }} /></div>
                      <span className="text-xs font-medium" style={{ color: difficultyConfig[q.difficulty || 'beginner'].color }}>{difficultyConfig[q.difficulty || 'beginner'].label}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mb-5">
                  <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 font-mono text-sm font-bold text-white">{idx + 1}</div>
                  <h2 className="font-display font-semibold text-white text-lg leading-snug">{q.q}</h2>
                </div>

                <div className="space-y-3">
                  {q.options.map((opt, oi) => (
                    <div key={oi} className="quiz-option">
                      <input type="radio" name={qKey} value={opt} id={`${qKey}_${oi}`} checked={answers[qKey] === opt} onChange={() => setAnswers(a => ({ ...a, [qKey]: opt }))} />
                      <label htmlFor={`${qKey}_${oi}`}>
                        <div className="radio-dot">{answers[qKey] === opt && <div className="w-2 h-2 rounded-full bg-dark-300" />}</div>
                        <span className="font-mono text-xs text-slate-500 mr-1">{String.fromCharCode(65 + oi)}.</span>
                        {opt}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {error && <div className="mb-3 text-red-400 text-sm">{error}</div>}

        <div className="flex items-center justify-between">
          <button type="button" onClick={() => setCurrentQ(q => Math.max(0, q - 1))} disabled={currentQ === 0} className="btn-cyber flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"><ChevronLeft size={16} />Previous</button>
          <div className="flex gap-1.5">{quizItems.map((q, i) => <button key={i} type="button" onClick={() => setCurrentQ(i)} className={`w-2 h-2 rounded-full transition-all ${i === currentQ ? 'w-6 bg-cyan-400' : answers[`${q.topic}_${q.index}`] ? 'bg-green-400/70' : 'bg-white/20'}`} />)}</div>
          {currentQ < total - 1 ? (
            <button type="button" onClick={() => setCurrentQ(q => q + 1)} className="btn-cyber flex items-center gap-2">Next<ChevronRight size={16} /></button>
          ) : (
            <button type="submit" disabled={!answeredAll} className={`btn-cyber-solid flex items-center gap-2 ${!answeredAll ? 'opacity-50 cursor-not-allowed' : ''}`}><Brain size={15} />Submit Quiz</button>
          )}
        </div>

        {!answeredAll && currentQ === total - 1 && <div className="mt-3 flex items-center gap-2 text-yellow-400 text-xs justify-center"><AlertCircle size={12} /><span>{total - Object.keys(answers).length} question(s) unanswered. Please answer all to submit.</span></div>}
      </form>
    </div>
  );
}
