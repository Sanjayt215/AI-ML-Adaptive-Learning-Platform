
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
  const [responseTimes, setResponseTimes] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Persistent pseudonymous learner_id and session tracking
  const learnerId = useMemo(() => {
    let id = localStorage.getItem('autolearn_learner_id');
    if (!id) {
      id = 'learner_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('autolearn_learner_id', id);
    }
    return id;
  }, []);

  const [questionStartTime, setQuestionStartTime] = useState(() => Date.now());

  // Record presentation start whenever active question index changes
  useEffect(() => {
    setQuestionStartTime(Date.now());
  }, [currentQ]);

  const loadQuiz = async (forceNew = false) => {
    setLoading(true);
    setError('');
    try {
      let data = await apiFetch(`/api/quiz${forceNew ? '?refresh=1' : ''}`);
      if (!data?.quizItems?.length) {
        // Auto-initialize plan if empty
        await apiFetch('/api/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            syllabus_text: 'Artificial Intelligence, Machine Learning, Reinforcement Learning',
            target_goal: 'Master AI & ML',
          }),
        });
        data = await apiFetch(`/api/quiz${forceNew ? '?refresh=1' : ''}`);
      }
      savePartial({ quizItems: Array.isArray(data?.quizItems) ? data.quizItems : [] });
      setAnswers({});
      setResponseTimes({});
      setCurrentQ(0);
      setQuestionStartTime(Date.now());
    } catch (err) {
      // Attempt auto-recovery once
      try {
        await apiFetch('/api/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            syllabus_text: 'Artificial Intelligence, Machine Learning, Reinforcement Learning',
            target_goal: 'Master AI & ML',
          }),
        });
        const recoveryData = await apiFetch(`/api/quiz${forceNew ? '?refresh=1' : ''}`);
        if (recoveryData?.quizItems?.length) {
          savePartial({ quizItems: recoveryData.quizItems });
          setAnswers({});
          setResponseTimes({});
          setCurrentQ(0);
          setQuestionStartTime(Date.now());
          return;
        }
      } catch {}
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

  const handleSelectOption = (qKey, opt) => {
    const elapsed = Date.now() - questionStartTime;
    setAnswers(a => ({ ...a, [qKey]: opt }));
    setResponseTimes(rt => {
      // Accumulate or record active interaction time for this question
      const prev = rt[qKey] || 0;
      return { ...rt, [qKey]: prev + Math.max(elapsed, 100) };
    });
    // Reset timer so further thinking on same question continues accumulating
    setQuestionStartTime(Date.now());
  };

  const difficultyConfig = {
    beginner: { label: 'Beginner', color: '#4ade80', pct: 30 },
    intermediate: { label: 'Intermediate', color: '#fbbf24', pct: 60 },
    advanced: { label: 'Advanced', color: '#f87171', pct: 90 },
    expert: { label: 'Expert', color: '#c084fc', pct: 100 },
  };

  const getDifficultyMeta = (difficulty) => {
    if (typeof difficulty === 'number') {
      if (difficulty <= 1) return { label: 'Level 1 (Beginner)', color: '#4ade80', pct: 25 };
      if (difficulty === 2) return { label: 'Level 2 (Easy)', color: '#38bdf8', pct: 50 };
      if (difficulty === 3) return { label: 'Level 3 (Intermediate)', color: '#fbbf24', pct: 75 };
      if (difficulty === 4) return { label: 'Level 4 (Advanced)', color: '#f87171', pct: 90 };
      return { label: `Level ${difficulty} (Mastery)`, color: '#c084fc', pct: 100 };
    }
    const key = String(difficulty || 'beginner').toLowerCase().trim();
    if (difficultyConfig[key]) return difficultyConfig[key];
    if (key.includes('easy') || key.includes('basic') || key.includes('intro')) {
      return difficultyConfig.beginner;
    }
    if (key.includes('mid') || key.includes('med') || key.includes('inter')) {
      return difficultyConfig.intermediate;
    }
    if (key.includes('hard') || key.includes('adv') || key.includes('expert')) {
      return difficultyConfig.advanced;
    }
    return difficultyConfig.beginner;
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
        body: JSON.stringify({
          answers,
          response_times: responseTimes,
          learner_id: learnerId,
        }),
      });
      
      // Validate and normalize response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid server response: expected object');
      }
      
      const normalizedData = normalizeQuizResponse(data);
      savePartial(normalizedData);
      
      const refreshed = await refresh();
      if (!refreshed) {
        throw new Error('Failed to refresh dashboard after quiz submission.');
      }
      navigate('/dashboard');
    } catch (err) {
      setSubmitted(false);
      console.error('Quiz submission error:', err);
      setError(err.message || 'Quiz submission failed. Please try again.');
    }
  };

  // Normalize quiz response to ensure consistent field structure
  const normalizeQuizResponse = (data) => {
    // Deep sanitize to remove any NaN values
    const sanitize = (obj) => {
      if (obj === null || obj === undefined) return null;
      if (typeof obj !== 'object') return obj;
      if (Array.isArray(obj)) {
        return obj.map(sanitize);
      }
      const cleaned = {};
      for (const key in obj) {
        let val = obj[key];
        // Remove NaN/Infinity
        if (typeof val === 'number' && !isFinite(val)) {
          val = null;
        }
        cleaned[key] = sanitize(val);
      }
      return cleaned;
    };

    const sanitized = sanitize(data);
    
    return {
      ...sanitized,
      assessment: (sanitized.assessment || []).map(item => ({
        topic: item.topic || 'Unknown',
        score_pct: typeof item.score_pct === 'number' ? item.score_pct : 0,
        predicted_level: item.predicted_level || 'beginner',
        predicted_exam_score: typeof item.predicted_exam_score === 'number' ? item.predicted_exam_score : 0,
        next_topics: Array.isArray(item.next_topics) ? item.next_topics : [],
      })),
      resources: (sanitized.resources || []).map(resource => ({
        topic: resource.topic || 'Unknown',
        level: resource.level || 'beginner',
        videos: (resource.videos || []).map(v => ({
          ...v,
          title: v.title || 'Untitled Video',
          channel: v.channel || 'Unknown Channel',
          url: v.url || '#',
          level: v.level || 'beginner',
        })),
        courses: (resource.courses || []).map(c => ({
          ...c,
          title: c.title || 'Untitled Course',
          provider: c.provider || c.platform || 'Unknown Provider',
          url: c.url || '#',
          level: c.level || 'beginner',
        })),
        datasets: (resource.datasets || []).map(d => ({
          ...d,
          title: d.title || 'Untitled Dataset',
          source: d.source || 'Unknown Source',
          url: d.url || '#',
          level: d.level || 'beginner',
        })),
        project: (typeof resource.project === 'string') ? resource.project : 
                 (typeof resource.project === 'object' && resource.project.project) ? resource.project.project :
                 'Practice a small project on this topic.',
      })),
      learningPath: (sanitized.learningPath || []).map(item => ({
        ...item,
        topic: item.topic || 'Unknown',
        level: item.level || 'beginner',
      })),
    };
  };

  if (loading && !total) {
    return (
      <div className="px-6 py-8 max-w-2xl mx-auto text-center">
        <div className="glass-card p-10 space-y-4">
          <div className="w-12 h-12 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
          <h2 className="font-display font-semibold text-lg text-white">Loading Adaptive Quiz...</h2>
          <p className="text-slate-400 text-sm">Preparing diagnostic questions tailored to your syllabus.</p>
        </div>
      </div>
    );
  }

  if (error && !total) {
    return (
      <div className="px-6 py-8 max-w-2xl mx-auto">
        <div className="glass-card p-8 text-center space-y-4 border-cyan-500/30">
          <div className="w-12 h-12 rounded-full bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center mx-auto text-cyan-400 font-bold">
            <Brain size={24} />
          </div>
          <div className="text-white text-lg font-display">Diagnostic Assessment Ready</div>
          <div className="text-slate-300 text-sm">
            {error.includes('Start your plan') ? 'Initialize your diagnostic study plan to generate adaptive questions.' : error}
          </div>
          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={async () => {
                setLoading(true);
                setError('');
                try {
                  await apiFetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      syllabus_text: 'Artificial Intelligence, Machine Learning, Reinforcement Learning',
                      target_goal: 'Master AI & ML',
                    }),
                  });
                  await loadQuiz(true);
                } catch (e) {
                  setError(e.message || 'Failed to initialize plan');
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-cyber-solid flex items-center gap-2"
            >
              <RefreshCcw size={14} /> Start Diagnostic Quiz
            </button>
            <button onClick={() => navigate('/learn')} className="btn-cyber">Go to My Learning</button>
          </div>
        </div>
      </div>
    );
  }

  if (!total) {
    return (
      <div className="px-6 py-8 max-w-2xl mx-auto">
        <div className="glass-card p-8 text-center space-y-4">
          <div className="text-white text-lg font-display">No quiz generated yet</div>
          <div className="text-slate-500 text-sm">Start by entering your syllabus or learning goal first.</div>
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

  const diff = getDifficultyMeta(item?.difficulty);

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
          if (!q || typeof q !== 'object') return null;
          const qKey = `${q.topic || 'topic'}_${q.index ?? idx}`;
          const qDiff = getDifficultyMeta(q.difficulty);
          const options = Array.isArray(q.options) ? q.options : [];
          return (
            <div key={qKey} style={{ display: idx === currentQ ? 'block' : 'none' }}>
              <div className="glass-card p-6 mb-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="px-3 py-1 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 text-xs font-semibold font-mono uppercase tracking-wider">{q.topic || 'General'}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Difficulty</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-20 difficulty-track"><div className="difficulty-fill" style={{ width: `${qDiff.pct}%`, background: qDiff.color }} /></div>
                      <span className="text-xs font-medium" style={{ color: qDiff.color }}>{qDiff.label}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mb-5">
                  <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 font-mono text-sm font-bold text-white">{idx + 1}</div>
                  <h2 className="font-display font-semibold text-white text-lg leading-snug">{q.q || q.question || 'Question text unavailable'}</h2>
                </div>

                <div className="space-y-3">
                  {options.map((opt, oi) => (
                    <div key={oi} className="quiz-option">
                      <input type="radio" name={qKey} value={opt} id={`${qKey}_${oi}`} checked={answers[qKey] === opt} onChange={() => handleSelectOption(qKey, opt)} />
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
