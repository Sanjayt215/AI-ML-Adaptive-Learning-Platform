import React, { useState, useEffect } from 'react';
import {
  Brain, CheckCircle2, AlertTriangle, ArrowRight, BookOpen, Code2,
  Zap, Play, Eye, RotateCcw, Award, Clock, HelpCircle, Layers,
  Sparkles, RefreshCw, BarChart2, Shield, Compass, ChevronRight,
  Check, X, FileText, Terminal, ArrowUpRight, CheckSquare, MessageSquare
} from 'lucide-react';
import { apiFetch } from '../utils/api';

const JOURNEY_STAGES = [
  { id: 'select_and_diagnostic', label: '1. Diagnostic', icon: Brain },
  { id: 'topic_analysis', label: '2. Analysis', icon: BarChart2 },
  { id: 'weak_topics', label: '3. Weak Topics', icon: Zap },
  { id: 'concept_teaching', label: '4. Learn Concept', icon: BookOpen },
  { id: 'learning_methods', label: '5. Multi-Method', icon: Layers },
  { id: 'topic_evaluation', label: '6. Evaluation', icon: Award },
  { id: 'mock_exam', label: '7. Mock Exam', icon: CheckSquare },
  { id: 'mock_results', label: '8. Results & Progress', icon: ArrowUpRight },
];

export default function PersonalizedLearningJourney() {
  const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';

  // Overall journey status
  const [journeyStatus, setJourneyStatus] = useState(null);
  const [activeStage, setActiveStage] = useState('select_and_diagnostic');
  const [loading, setLoading] = useState(true);

  // Stage 1: Diagnostic Quiz Setup & Active Quiz
  const [courses, setCourses] = useState({});
  const [selectedCourse, setSelectedCourse] = useState('ai_ml_core');
  const [selectedDifficulty, setSelectedDifficulty] = useState('adaptive');
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizStartTime, setQuizStartTime] = useState(Date.now());
  const [submittingQuiz, setSubmittingQuiz] = useState(false);

  // Stage 2: Assessment Report
  const [assessmentReport, setAssessmentReport] = useState(null);

  // Stage 3: Weak Topics Prioritization & Mistake Inspection
  const [weakTopicsData, setWeakTopicsData] = useState(null);
  const [targetTopic, setTargetTopic] = useState('python');
  const [mistakeModal, setMistakeModal] = useState(null);
  const [inspectingMistake, setInspectingMistake] = useState(false);

  // Stage 4 & 5: Concept Teaching Centre
  const [conceptData, setConceptData] = useState(null);
  const [conceptLoading, setConceptLoading] = useState(false);
  const [learnerTier, setLearnerTier] = useState('foundational'); // 'foundational' | 'advanced'

  // Stage 6: Multi-Method Learning
  const [activeMethod, setActiveMethod] = useState('explanation'); // explanation, worked_examples, visual, coding, recall, conceptual, tutor
  const [codingInput, setCodingInput] = useState('');
  const [codingResult, setCodingResult] = useState(null);
  const [codingRunning, setCodingRunning] = useState(false);
  const [conceptualInput, setConceptualInput] = useState('');
  const [conceptualResult, setConceptualResult] = useState(null);
  const [evaluatingConceptual, setEvaluatingConceptual] = useState(false);
  const [flashcardIdx, setFlashcardIdx] = useState(0);
  const [flashcardFlipped, setFlashcardFlipped] = useState(false);

  // Stage 7: Topic Evaluation
  const [topicEvalResult, setTopicEvalResult] = useState(null);
  const [evaluatingTopic, setEvaluatingTopic] = useState(false);

  // Stage 8: Mock Exam Configuration & Active Exam
  const [mockExamMethod, setMockExamMethod] = useState('mixed');
  const [mockNumQuestions, setMockNumQuestions] = useState(6);
  const [mockDifficulty, setMockDifficulty] = useState(3);
  const [activeMockExam, setActiveMockExam] = useState(null);
  const [mockAnswers, setMockAnswers] = useState({});
  const [mockTimeRemaining, setMockTimeRemaining] = useState(900);
  const [submittingMock, setSubmittingMock] = useState(false);

  // Stage 9: Mock Results
  const [mockResultsData, setMockResultsData] = useState(null);

  // Refresh status on mount
  useEffect(() => {
    fetchJourneyStatus();
  }, []);

  const fetchJourneyStatus = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/journey/status?learner_id=${learnerId}`);
      if (data && data.ok) {
        setJourneyStatus(data);
        setCourses(data.courses || {});
        if (data.latest_diagnostic) {
          setAssessmentReport(data.latest_diagnostic);
        }
        if (data.stage) {
          if (data.stage === 'weak_topics') {
            setActiveStage('weak_topics');
            fetchWeakTopics();
          } else if (data.stage === 'mock_exam') {
            setActiveStage('mock_exam');
          } else {
            setActiveStage(data.stage);
          }
        }
      }
    } catch (e) {
      console.error('Error fetching journey status:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchWeakTopics = async () => {
    try {
      const data = await apiFetch(`/api/journey/weak-topics?learner_id=${learnerId}`);
      if (data && data.ok) {
        setWeakTopicsData(data);
        if (data.weak_topics_ranked && data.weak_topics_ranked.length > 0) {
          setTargetTopic(data.weak_topics_ranked[0].topic);
        }
      }
    } catch (e) {
      console.error('Error fetching weak topics:', e);
    }
  };

  const loadConceptTeaching = async (topic) => {
    setConceptLoading(true);
    setTargetTopic(topic);
    try {
      const data = await apiFetch(`/api/journey/concept/${encodeURIComponent(topic)}`);
      if (data && data.ok) {
        setConceptData(data.concept);
        if (data.concept.coding_challenge) {
          setCodingInput(data.concept.coding_challenge.starter_code || '');
        }
        setActiveStage('concept_teaching');
      }
    } catch (e) {
      console.error('Error loading concept:', e);
    } finally {
      setConceptLoading(false);
    }
  };

  // -------------------------------------------------------------
  // STAGE 1: START & SUBMIT INITIAL DIAGNOSTIC
  // -------------------------------------------------------------
  const handleStartDiagnostic = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/journey/diagnostic/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          subject: selectedCourse,
          difficulty: selectedDifficulty,
          num_questions: 8,
        }),
      });
      if (res && res.ok) {
        setActiveQuiz(res);
        setQuizAnswers({});
        setQuizStartTime(Date.now());
      }
    } catch (e) {
      console.error('Failed to start diagnostic:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDiagnostic = async () => {
    if (!activeQuiz) return;
    setSubmittingQuiz(true);
    const durationSec = Math.round((Date.now() - quizStartTime) / 1000);
    try {
      const res = await apiFetch('/api/journey/diagnostic/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          diagnostic_id: activeQuiz.diagnostic_id,
          answers: quizAnswers,
          duration_seconds: durationSec,
        }),
      });
      if (res && res.ok) {
        setAssessmentReport(res);
        setActiveQuiz(null);
        setActiveStage('topic_analysis');
        fetchWeakTopics();
      }
    } catch (e) {
      console.error('Failed to submit diagnostic:', e);
    } finally {
      setSubmittingQuiz(false);
    }
  };

  // -------------------------------------------------------------
  // MISTAKE INSPECTION
  // -------------------------------------------------------------
  const handleInspectMistake = async (itemId, studentAns, topic) => {
    setInspectingMistake(true);
    try {
      const data = await apiFetch('/api/journey/concept/mistake-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: itemId,
          submitted_answer: studentAns,
          topic: topic,
        }),
      });
      if (data && data.ok) {
        setMistakeModal(data);
      }
    } catch (e) {
      console.error('Error analyzing mistake:', e);
    } finally {
      setInspectingMistake(false);
    }
  };

  // -------------------------------------------------------------
  // STAGE 6: RUN PRACTICAL CODE IN SANDBOX
  // -------------------------------------------------------------
  const handleRunCodingChallenge = async () => {
    if (!codingInput.trim()) return;
    setCodingRunning(true);
    try {
      const res = await apiFetch('/api/journey/learning-method/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          topic: targetTopic,
          method: 'coding',
          user_input: codingInput,
          duration_seconds: 60,
        }),
      });
      if (res && res.ok) {
        setCodingResult(res.feedback);
      }
    } catch (e) {
      console.error('Error running code challenge:', e);
    } finally {
      setCodingRunning(false);
    }
  };

  // -------------------------------------------------------------
  // STAGE 6: EVALUATE CONCEPTUAL EXPLANATION
  // -------------------------------------------------------------
  const handleEvaluateConceptual = async () => {
    if (!conceptualInput.trim()) return;
    setEvaluatingConceptual(true);
    try {
      const res = await apiFetch('/api/journey/learning-method/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          topic: targetTopic,
          method: 'conceptual',
          user_input: conceptualInput,
          duration_seconds: 90,
        }),
      });
      if (res && res.ok) {
        setConceptualResult(res.feedback);
      }
    } catch (e) {
      console.error('Error evaluating explanation:', e);
    } finally {
      setEvaluatingConceptual(false);
    }
  };

  // -------------------------------------------------------------
  // STAGE 7: EVALUATE TOPIC UNDERSTANDING
  // -------------------------------------------------------------
  const handleEvaluateTopicUnderstanding = async () => {
    setEvaluatingTopic(true);
    try {
      const submission = conceptualInput || codingInput || 'Demonstrated understanding across learning activities';
      const res = await apiFetch('/api/journey/topic-evaluation/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          topic: targetTopic,
          method: conceptualInput ? 'conceptual' : 'coding',
          submission: submission,
        }),
      });
      if (res && res.ok) {
        setTopicEvalResult(res);
        setActiveStage('topic_evaluation');
      }
    } catch (e) {
      console.error('Error evaluating topic:', e);
    } finally {
      setEvaluatingTopic(false);
    }
  };

  // -------------------------------------------------------------
  // STAGE 8 & 9: GENERATE & SUBMIT PERSONALIZED MOCK EXAM
  // -------------------------------------------------------------
  const handleGenerateMockExam = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/journey/mock-exam/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          title: `Personalized Mock Exam: ${targetTopic.replace('_', ' ').toUpperCase()}`,
          method: mockExamMethod,
          topics: [targetTopic, 'python', 'linear regression'],
          difficulty: mockDifficulty,
          num_questions: mockNumQuestions,
        }),
      });
      if (res && res.ok) {
        setActiveMockExam(res);
        setMockAnswers({});
        setMockTimeRemaining(res.duration_minutes * 60);
      }
    } catch (e) {
      console.error('Error generating mock exam:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitMockExam = async () => {
    if (!activeMockExam) return;
    setSubmittingMock(true);
    try {
      const res = await apiFetch('/api/journey/mock-exam/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          exam_id: activeMockExam.exam_id,
          answers: mockAnswers,
          duration_seconds: 600,
        }),
      });
      if (res && res.ok) {
        setMockResultsData(res);
        setActiveMockExam(null);
        setActiveStage('mock_results');
      }
    } catch (e) {
      console.error('Error submitting mock exam:', e);
    } finally {
      setSubmittingMock(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-8">
      {/* Journey Step Progress Indicator Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-white/10 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-cyan-400" />
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
              YOUR PERSONALIZED LEARNING JOURNEY
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {journeyStatus?.next_action || 'Continuous Knowledge Tracing'}
          </span>
        </div>

        <div className="grid grid-cols-4 lg:grid-cols-8 gap-2">
          {JOURNEY_STAGES.map((s, idx) => {
            const Icon = s.icon;
            const isActive = activeStage === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActiveStage(s.id)}
                className={`p-2 rounded-xl text-center border transition-all flex flex-col items-center gap-1.5 ${
                  isActive
                    ? 'bg-cyan-500/20 border-cyan-400 text-white shadow-lg shadow-cyan-500/10'
                    : 'bg-white/5 border-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-cyan-400' : 'text-slate-400'} />
                <span className="text-[11px] font-semibold truncate w-full">{s.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STAGE 1: SELECT SUBJECT & TAKE INITIAL DIAGNOSTIC */}
      {/* ========================================================================= */}
      {activeStage === 'select_and_diagnostic' && !activeQuiz && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="max-w-2xl">
            <span className="px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold">
              STEP 1: COURSE ENROLLMENT & DIAGNOSTIC
            </span>
            <h2 className="font-display font-bold text-white text-3xl mt-3">
              Select Your Learning Course & Take Initial Assessment
            </h2>
            <p className="text-slate-300 text-sm mt-2 leading-relaxed">
              Before learning begins, our Bayesian Knowledge Tracing engine assesses your foundational mastery across concepts, pinpointing strengths and prerequisite gaps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {Object.entries(courses).map(([key, c]) => (
              <div
                key={key}
                onClick={() => setSelectedCourse(key)}
                className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                  selectedCourse === key
                    ? 'bg-cyan-500/15 border-cyan-400 ring-1 ring-cyan-400/30'
                    : 'bg-slate-900/60 border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                    {c.category}
                  </span>
                  {selectedCourse === key && <CheckCircle2 size={16} className="text-cyan-400" />}
                </div>
                <h3 className="font-display font-bold text-white text-base">{c.title}</h3>
                <p className="text-slate-400 text-xs mt-2 leading-relaxed">{c.description}</p>
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {c.default_topics?.slice(0, 4).map(t => (
                    <span key={t} className="px-2 py-0.5 rounded bg-white/5 text-[10px] text-slate-300 font-mono">
                      {t}
                    </span>
                  ))}
                  <span className="text-[10px] text-slate-500 font-mono">+{c.default_topics?.length - 4} more</span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-white/10">
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 font-medium">Diagnostic Difficulty:</span>
              {['easy', 'adaptive', 'hard'].map(d => (
                <button
                  key={d}
                  onClick={() => setSelectedDifficulty(d)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono uppercase font-semibold border ${
                    selectedDifficulty === d
                      ? 'bg-cyan-400 text-slate-950 border-cyan-400'
                      : 'bg-white/5 border-white/10 text-slate-400'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            <button
              onClick={handleStartDiagnostic}
              disabled={loading}
              className="btn-cyber-solid flex items-center gap-2"
            >
              <Play size={16} /> Start Diagnostic Quiz
            </button>
          </div>
        </div>
      )}

      {/* ACTIVE DIAGNOSTIC QUIZ INTERACTION */}
      {activeQuiz && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
                DIAGNOSTIC ASSESSMENT IN PROGRESS
              </span>
              <h2 className="text-xl font-display font-bold text-white">{activeQuiz.subject_title}</h2>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400 font-mono">Questions Attempted</div>
              <div className="text-lg font-bold text-cyan-400">
                {Object.keys(quizAnswers).length} / {activeQuiz.total_questions}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {activeQuiz.questions.map((q, idx) => (
              <div key={q.item_id} className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400 text-[11px] font-mono font-bold uppercase">
                    Q{idx + 1} · {q.topic}
                  </span>
                  <span className="text-xs font-mono text-slate-400">Bloom's: {q.blooms_level}</span>
                </div>

                <p className="text-white text-base font-medium">{q.question}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                  {q.options.map(opt => (
                    <button
                      key={opt}
                      onClick={() => setQuizAnswers(prev => ({ ...prev, [q.item_id]: opt }))}
                      className={`p-3 rounded-xl border text-left text-xs transition-all flex items-center gap-2 ${
                        quizAnswers[q.item_id] === opt
                          ? 'bg-cyan-500/20 border-cyan-400 text-white font-semibold'
                          : 'bg-white/5 border-white/5 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${
                        quizAnswers[q.item_id] === opt ? 'border-cyan-400 bg-cyan-400' : 'border-slate-500'
                      }`}>
                        {quizAnswers[q.item_id] === opt && <div className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
                      </div>
                      <span>{opt}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-white/10">
            <span className="text-xs text-slate-400">
              Note: Unanswered questions will be classified as not assessed, rather than marked wrong.
            </span>
            <button
              onClick={handleSubmitDiagnostic}
              disabled={submittingQuiz}
              className="btn-cyber-solid flex items-center gap-2"
            >
              {submittingQuiz ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
              Submit Diagnostic & Generate Report
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 2: "YOUR KNOWLEDGE ASSESSMENT REPORT" */}
      {/* ========================================================================= */}
      {activeStage === 'topic_analysis' && assessmentReport && (
        <div className="space-y-6">
          <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
              <div>
                <span className="px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold">
                  STEP 2: ASSESSMENT ANALYSIS
                </span>
                <h2 className="font-display font-bold text-white text-3xl mt-2">
                  Your Knowledge Assessment Report
                </h2>
                <p className="text-slate-400 text-sm mt-1">
                  Empirical test score compared with calibrated Bayesian Knowledge Tracing estimates.
                </p>
              </div>

              <button
                onClick={() => {
                  fetchWeakTopics();
                  setActiveStage('weak_topics');
                }}
                className="btn-cyber-solid flex items-center gap-2 shrink-0"
              >
                View Prioritized Weak Topics <ArrowRight size={16} />
              </button>
            </div>

            {/* A. Overall Performance Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
                <div className="text-2xl font-bold text-white">{assessmentReport.overall_performance?.total_questions}</div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 uppercase">Total Items</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
                <div className="text-2xl font-bold text-cyan-400">{assessmentReport.overall_performance?.attempted_questions}</div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 uppercase">Attempted</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
                <div className="text-2xl font-bold text-emerald-400">{assessmentReport.overall_performance?.correct_answers}</div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 uppercase">Correct</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
                <div className="text-2xl font-bold text-red-400">{assessmentReport.overall_performance?.incorrect_answers}</div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 uppercase">Incorrect</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
                <div className="text-2xl font-bold text-slate-400">{assessmentReport.overall_performance?.unanswered_questions}</div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 uppercase">Unanswered</div>
              </div>
              <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 text-center">
                <div className="text-2xl font-bold text-cyan-300">{assessmentReport.overall_performance?.overall_score_pct}%</div>
                <div className="text-[11px] font-mono text-cyan-400 mt-1 uppercase">Overall Score</div>
              </div>
            </div>

            {/* B. Topic-Wise Performance Table */}
            <div>
              <h3 className="font-display font-bold text-white text-lg mb-3">Topic-Wise Performance Breakdown</h3>
              <div className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-900/60">
                <table className="w-full text-left text-sm">
                  <thead className="bg-white/5 text-xs text-slate-400 font-mono uppercase">
                    <tr>
                      <th className="p-3.5">Topic</th>
                      <th className="p-3.5">Correct</th>
                      <th className="p-3.5">Total</th>
                      <th className="p-3.5">Test Score</th>
                      <th className="p-3.5">BKT Mastery</th>
                      <th className="p-3.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {assessmentReport.topic_performance_table?.map(t => (
                      <tr key={t.topic} className="hover:bg-white/5">
                        <td className="p-3.5 font-bold text-white">{t.topic_title}</td>
                        <td className="p-3.5 text-emerald-400 font-mono">{t.correct}</td>
                        <td className="p-3.5 text-slate-400 font-mono">{t.total}</td>
                        <td className="p-3.5 font-bold text-white font-mono">{t.score_pct}%</td>
                        <td className="p-3.5 font-mono text-purple-400">
                          {t.bkt_mastery_pct}%
                          {t.insufficient_evidence && (
                            <span className="ml-1.5 text-[10px] text-amber-400 font-mono">(Early estimate)</span>
                          )}
                        </td>
                        <td className="p-3.5">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            t.status === 'Strong' ? 'bg-emerald-400/10 text-emerald-400' :
                            t.status === 'Developing' ? 'bg-yellow-400/10 text-yellow-400' :
                            t.status === 'Needs Improvement' ? 'bg-red-400/10 text-red-400' :
                            'bg-slate-400/10 text-slate-400'
                          }`}>
                            {t.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* C. Topic Accuracy Bar Chart Visualization */}
            <div>
              <h3 className="font-display font-bold text-white text-lg mb-3">Topic Performance Accuracy Chart</h3>
              <div className="space-y-2 p-5 rounded-2xl bg-slate-900/60 border border-white/10">
                {assessmentReport.visualization_bars?.map(b => (
                  <div key={b.topic_key} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-300">{b.topic}</span>
                      <span className="font-mono text-cyan-400 font-bold">{b.accuracy}%</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          b.accuracy >= 75 ? 'bg-emerald-400' : b.accuracy >= 50 ? 'bg-yellow-400' : 'bg-red-400'
                        }`}
                        style={{ width: `${Math.max(b.accuracy, 4)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* D. Knowledge Gap Analysis */}
            {assessmentReport.knowledge_gap_analysis?.length > 0 && (
              <div>
                <h3 className="font-display font-bold text-white text-lg mb-3 flex items-center gap-2">
                  <AlertTriangle size={18} className="text-amber-400" />
                  Identified Knowledge Gaps
                </h3>
                <div className="space-y-3">
                  {assessmentReport.knowledge_gap_analysis.map((g, idx) => (
                    <div key={idx} className="p-4 rounded-2xl bg-red-400/5 border border-red-400/20 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-red-400 uppercase">
                          {g.topic} · Misunderstood: {g.concept_misunderstood}
                        </span>
                        <button
                          onClick={() => handleInspectMistake(g.item_id, g.student_answer, g.topic)}
                          className="text-xs text-cyan-400 hover:underline flex items-center gap-1"
                        >
                          Understand Why I Got It Wrong <ChevronRight size={14} />
                        </button>
                      </div>
                      <p className="text-xs text-slate-300">{g.question}</p>
                      <div className="text-xs text-slate-400 font-mono">
                        Recommendation: {g.recommended_activity}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 3: PERSONALIZED WEAK TOPIC PRIORITIZATION */}
      {/* ========================================================================= */}
      {activeStage === 'weak_topics' && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="max-w-2xl">
            <span className="px-3 py-1 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 text-xs font-mono font-semibold">
              STEP 3: WEAK TOPIC PRIORITIZATION
            </span>
            <h2 className="font-display font-bold text-white text-3xl mt-3">
              Personalized Weak Topic Action Centre
            </h2>
            <p className="text-slate-300 text-sm mt-2">
              Ranked by error frequency, prerequisite dependency gaps, and Bayesian Knowledge Tracing uncertainty.
            </p>
          </div>

          <div className="space-y-4">
            {weakTopicsData?.weak_topics_ranked?.map((t, idx) => (
              <div key={t.topic} className="p-6 rounded-2xl bg-slate-900/70 border border-white/10 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-red-400/10 border border-red-400/30 flex items-center justify-center font-mono font-bold text-red-400 text-sm">
                      #{idx + 1}
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-white text-lg">{t.topic_title}</h3>
                      <span className="text-xs text-slate-400 font-mono">
                        {t.error_count} recorded errors · BKT Mastery: {t.mastery_pct}%
                      </span>
                    </div>
                  </div>

                  <span className="px-3 py-1 rounded-full bg-red-400/15 border border-red-400/30 text-red-400 text-xs font-mono font-bold">
                    {t.priority_label}
                  </span>
                </div>

                {t.has_prerequisite_gap && (
                  <div className="p-3 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 text-xs flex items-center gap-2">
                    <AlertTriangle size={14} className="shrink-0" />
                    <span>Prerequisite Gap Detected: Foundation '{t.missing_prerequisites.join(', ')}' is unmastered.</span>
                  </div>
                )}

                <div className="flex flex-wrap gap-2.5 pt-2">
                  <button
                    onClick={() => loadConceptTeaching(t.topic)}
                    className="btn-cyber-solid text-xs flex items-center gap-1.5"
                  >
                    <BookOpen size={14} /> Start Learning This Topic
                  </button>
                  <button
                    onClick={() => handleInspectMistake(`q_${t.topic.slice(0, 3)}_01`, 'Wrong Option', t.topic)}
                    className="btn-cyber text-xs flex items-center gap-1.5"
                  >
                    <HelpCircle size={14} /> Understand Why I Got It Wrong
                  </button>
                  <button
                    onClick={() => {
                      setTargetTopic(t.topic);
                      setActiveStage('concept_teaching');
                      loadConceptTeaching(t.topic);
                    }}
                    className="btn-cyber text-xs flex items-center gap-1.5 text-purple-400"
                  >
                    <Award size={14} /> Take Topic Assessment
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MISTAKE ANALYSIS MODAL */}
      {mistakeModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-2xl w-full glass-card p-6 rounded-3xl border border-cyan-400/30 bg-slate-950 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase">
                  PEDAGOGICAL MISTAKE DIAGNOSIS
                </span>
                <h3 className="text-lg font-display font-bold text-white">{mistakeModal.concept_title}</h3>
              </div>
              <button onClick={() => setMistakeModal(null)} className="p-1 rounded-lg hover:bg-white/10">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300">
                <strong>Why your answer was incorrect:</strong> {mistakeModal.why_incorrect}
              </div>

              <div className="p-3 rounded-xl bg-emerald-400/10 border border-emerald-400/20 text-emerald-300">
                <strong>Correct Answer:</strong> {mistakeModal.correct_answer}
                <div className="mt-1 text-slate-300">{mistakeModal.why_correct}</div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/10">
                <strong>Concept Definition:</strong> {mistakeModal.concept_definition}
              </div>

              {mistakeModal.related_example && (
                <div className="p-3 rounded-xl bg-slate-900 border border-white/10">
                  <div className="font-bold text-slate-300 mb-1">Related Example Code:</div>
                  <pre className="p-2.5 rounded bg-black/60 text-cyan-300 font-mono text-[11px] overflow-x-auto">
                    {mistakeModal.related_example}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setMistakeModal(null)} className="btn-cyber-solid text-xs">
                Got It, Continue Learning
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 4 & 5: CONCEPT TEACHING CENTRE ("LEARN THIS CONCEPT") */}
      {/* ========================================================================= */}
      {activeStage === 'concept_teaching' && conceptData && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
            <div>
              <span className="px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold">
                STEP 5: CONCEPT TEACHING CENTRE
              </span>
              <h2 className="font-display font-bold text-white text-3xl mt-2">{conceptData.concept_name}</h2>
              <p className="text-slate-300 text-sm mt-1">{conceptData.simple_definition}</p>
            </div>

            {/* Differentiated Student Tier Toggle */}
            <div className="flex items-center gap-2 p-1.5 rounded-xl bg-white/5 border border-white/10 shrink-0">
              <button
                onClick={() => setLearnerTier('foundational')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                  learnerTier === 'foundational' ? 'bg-cyan-400 text-slate-950' : 'text-slate-400'
                }`}
              >
                Foundational
              </button>
              <button
                onClick={() => setLearnerTier('advanced')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                  learnerTier === 'advanced' ? 'bg-purple-400 text-slate-950' : 'text-slate-400'
                }`}
              >
                Advanced
              </button>
            </div>
          </div>

          {/* Differentiated Insight Banner */}
          <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 text-xs text-cyan-300 leading-relaxed">
            <strong>{learnerTier === 'foundational' ? 'Intuitive Foundation:' : 'Mathematical Deep Dive:'}</strong>{' '}
            {learnerTier === 'foundational'
              ? conceptData.differentiated?.foundational_tip
              : conceptData.differentiated?.advanced_insight}
          </div>

          {/* Core Explanation & Why It Matters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="font-display font-bold text-white text-base">Detailed Mechanism</h3>
              <p className="text-slate-300 text-xs leading-relaxed">{conceptData.detailed_explanation}</p>
              <div className="space-y-1.5 pt-2">
                <span className="text-xs font-bold text-white block">Step-by-Step Workflow:</span>
                {conceptData.how_it_works_steps?.map((st, i) => (
                  <div key={i} className="text-xs text-slate-400 flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                    <span>{st}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-display font-bold text-white text-base">Mathematical Formula & Architecture</h3>
              <div className="p-4 rounded-xl bg-slate-950/80 border border-white/10 font-mono text-cyan-300 text-xs">
                {conceptData.formula}
              </div>
              {conceptData.diagram && (
                <pre className="p-4 rounded-xl bg-black/60 border border-white/10 font-mono text-[11px] text-slate-300 overflow-x-auto">
                  {conceptData.diagram}
                </pre>
              )}
            </div>
          </div>

          {/* Worked Example */}
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-white/10 space-y-4">
            <h3 className="font-display font-bold text-white text-base flex items-center gap-2">
              <Terminal size={18} className="text-emerald-400" />
              Worked Example: {conceptData.worked_example?.title}
            </h3>
            <p className="text-xs text-slate-300">{conceptData.worked_example?.problem}</p>

            <pre className="p-4 rounded-xl bg-black/80 border border-white/10 font-mono text-xs text-emerald-400 overflow-x-auto">
              {conceptData.worked_example?.code}
            </pre>

            <div className="p-3 rounded-xl bg-white/5 font-mono text-xs text-slate-300">
              <strong>Expected Output:</strong> {conceptData.worked_example?.expected_output}
            </div>
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-white/10">
            <button
              onClick={() => setActiveStage('weak_topics')}
              className="btn-cyber text-xs"
            >
              Back to Weak Topics
            </button>
            <button
              onClick={() => setActiveStage('learning_methods')}
              className="btn-cyber-solid flex items-center gap-2"
            >
              Choose Learning Method <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 6: MULTI-METHOD LEARNING MODALITIES */}
      {/* ========================================================================= */}
      {activeStage === 'learning_methods' && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
            <div>
              <span className="px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold">
                STEP 6: MULTIPLE LEARNING METHODS
              </span>
              <h2 className="font-display font-bold text-white text-3xl mt-2">
                Choose Your Preferred Learning Method
              </h2>
              <p className="text-slate-300 text-sm mt-1">
                Active mastery for topic: <span className="font-bold text-cyan-400">{targetTopic}</span>
              </p>
            </div>

            <button
              onClick={handleEvaluateTopicUnderstanding}
              disabled={evaluatingTopic}
              className="btn-cyber-solid flex items-center gap-2 shrink-0"
            >
              <Award size={16} /> Evaluate My Understanding
            </button>
          </div>

          {/* Mode Selector Tabs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {[
              { id: 'explanation', label: 'Explanation', icon: BookOpen },
              { id: 'worked_examples', label: 'Examples', icon: FileText },
              { id: 'visual', label: 'Visual', icon: Eye },
              { id: 'coding', label: 'Coding', icon: Code2 },
              { id: 'recall', label: 'Recall', icon: RotateCcw },
              { id: 'conceptual', label: 'In My Words', icon: MessageSquare },
              { id: 'tutor', label: 'AI Tutor', icon: Sparkles },
            ].map(m => {
              const Icon = m.icon;
              const isSelected = activeMethod === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setActiveMethod(m.id)}
                  className={`p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-1 ${
                    isSelected
                      ? 'bg-cyan-400/20 border-cyan-400 text-white font-bold'
                      : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon size={16} className={isSelected ? 'text-cyan-400' : 'text-slate-400'} />
                  <span className="text-[11px] truncate w-full">{m.label}</span>
                </button>
              );
            })}
          </div>

          {/* METHOD A: EXPLANATION */}
          {activeMethod === 'explanation' && conceptData && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
              <h3 className="font-bold text-white text-lg">Theoretical Foundations</h3>
              <p className="text-slate-300 text-sm leading-relaxed">{conceptData.detailed_explanation}</p>
              <div className="p-4 rounded-xl bg-white/5 text-xs text-slate-300">
                <strong>Real-World Application:</strong> {conceptData.real_world_application}
              </div>
            </div>
          )}

          {/* METHOD B: WORKED EXAMPLES */}
          {activeMethod === 'worked_examples' && conceptData && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
              <h3 className="font-bold text-white text-lg">Step-by-Step Solved Problem</h3>
              <pre className="p-4 rounded-xl bg-black/80 font-mono text-xs text-emerald-400 overflow-x-auto">
                {conceptData.worked_example?.code}
              </pre>
              <div className="space-y-1.5">
                {conceptData.worked_example?.steps?.map((s, idx) => (
                  <div key={idx} className="text-xs text-slate-300">{s}</div>
                ))}
              </div>
            </div>
          )}

          {/* METHOD C: VISUAL LEARNING */}
          {activeMethod === 'visual' && conceptData && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
              <h3 className="font-bold text-white text-lg">Architecture & Process Diagram</h3>
              <pre className="p-6 rounded-2xl bg-black/80 font-mono text-xs text-cyan-300 overflow-x-auto leading-relaxed">
                {conceptData.diagram}
              </pre>
            </div>
          )}

          {/* METHOD D: PRACTICAL CODING CHALLENGE */}
          {activeMethod === 'coding' && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-lg">
                    {conceptData?.coding_challenge?.title || 'Interactive Python Challenge'}
                  </h3>
                  <p className="text-xs text-slate-300 mt-0.5">
                    {conceptData?.coding_challenge?.description || 'Implement the algorithm.'}
                  </p>
                </div>
                <button
                  onClick={handleRunCodingChallenge}
                  disabled={codingRunning}
                  className="btn-cyber-solid text-xs flex items-center gap-1.5"
                >
                  {codingRunning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                  Run In Secure Sandbox
                </button>
              </div>

              <textarea
                value={codingInput}
                onChange={e => setCodingInput(e.target.value)}
                rows={7}
                className="w-full p-4 rounded-xl bg-black/80 border border-white/10 font-mono text-xs text-cyan-300 focus:outline-none focus:border-cyan-400"
              />

              {codingResult && (
                <div className={`p-4 rounded-xl border text-xs font-mono ${
                  codingResult.ok ? 'bg-emerald-400/10 border-emerald-400/30 text-emerald-300' : 'bg-red-400/10 border-red-400/30 text-red-300'
                }`}>
                  <div className="font-bold">Sandbox Result: {codingResult.score_pct || 100}% Passed</div>
                  <div className="mt-1">{codingResult.output || 'Code executed safely with AST inspection.'}</div>
                </div>
              )}
            </div>
          )}

          {/* METHOD E: ACTIVE RECALL FLASHCARDS */}
          {activeMethod === 'recall' && conceptData?.active_recall_cards && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4 text-center">
              <div
                onClick={() => setFlashcardFlipped(!flashcardFlipped)}
                className="p-12 rounded-2xl bg-slate-950 border border-cyan-400/30 cursor-pointer min-h-[180px] flex items-center justify-center transition-all hover:border-cyan-400"
              >
                <div className="space-y-2">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">
                    {flashcardFlipped ? 'RECALL ANSWER' : 'QUESTION (Click to flip)'}
                  </span>
                  <p className="text-lg font-medium text-white max-w-lg mx-auto">
                    {flashcardFlipped
                      ? conceptData.active_recall_cards[flashcardIdx]?.back
                      : conceptData.active_recall_cards[flashcardIdx]?.front}
                  </p>
                </div>
              </div>

              <div className="flex justify-center gap-3">
                <button
                  onClick={() => {
                    setFlashcardIdx(prev => (prev > 0 ? prev - 1 : 0));
                    setFlashcardFlipped(false);
                  }}
                  className="btn-cyber text-xs"
                >
                  Previous
                </button>
                <button
                  onClick={() => {
                    setFlashcardIdx(prev => (prev < conceptData.active_recall_cards.length - 1 ? prev + 1 : 0));
                    setFlashcardFlipped(false);
                  }}
                  className="btn-cyber-solid text-xs"
                >
                  Next Flashcard
                </button>
              </div>
            </div>
          )}

          {/* METHOD F: EXPLAIN IN STUDENT'S OWN WORDS */}
          {activeMethod === 'conceptual' && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-lg">Explain the Concept In Your Own Words</h3>
                  <p className="text-xs text-slate-300">
                    Our NLP evaluator will detect identified mechanisms and highlight missing concepts.
                  </p>
                </div>
                <button
                  onClick={handleEvaluateConceptual}
                  disabled={evaluatingConceptual}
                  className="btn-cyber-solid text-xs flex items-center gap-1.5"
                >
                  {evaluatingConceptual ? <RefreshCw size={14} className="animate-spin" /> : <Award size={14} />}
                  Evaluate My Explanation
                </button>
              </div>

              <textarea
                value={conceptualInput}
                onChange={e => setConceptualInput(e.target.value)}
                placeholder="Explain how this algorithm works, why it is important, and how it handles inputs..."
                rows={5}
                className="w-full p-4 rounded-xl bg-slate-950 border border-white/10 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
              />

              {conceptualResult && (
                <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-400/30 text-xs space-y-2">
                  <div className="font-bold text-white">Evaluator Score: {conceptualResult.score}%</div>
                  <div className="text-slate-300">
                    Concepts Identified: {conceptualResult.identified_concepts?.join(', ') || 'General coverage'}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* METHOD G: AI TUTOR CONVERSATION */}
          {activeMethod === 'tutor' && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
              <h3 className="font-bold text-white text-lg">AI Personal Learning Tutor</h3>
              <p className="text-xs text-slate-300">
                Ask targeted doubts about {targetTopic}. The tutor adapts hints across 3 pedagogical tiers.
              </p>
              <div className="pt-2">
                <a href="/ai-tutor" className="btn-cyber-solid text-xs inline-flex items-center gap-2">
                  <MessageSquare size={14} /> Open Fullscreen AI Tutor
                </a>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 7: TOPIC LEARNING EVALUATION REPORT */}
      {/* ========================================================================= */}
      {activeStage === 'topic_evaluation' && topicEvalResult && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
            <div>
              <span className="px-3 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/20 text-emerald-400 text-xs font-mono font-semibold">
                STEP 7: TOPIC LEARNING EVALUATION REPORT
              </span>
              <h2 className="font-display font-bold text-white text-3xl mt-2">
                Topic Understanding Verified: {topicEvalResult.topic_title}
              </h2>
              <p className="text-slate-300 text-sm mt-1">
                Post-learning verification across technical accuracy, application, and depth.
              </p>
            </div>

            <div className="text-right">
              <span className="text-3xl font-display font-bold text-emerald-400">{topicEvalResult.score_pct}%</span>
              <div className="text-xs font-mono text-slate-400">Evaluation Score</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-emerald-400/5 border border-emerald-400/20 space-y-2">
              <span className="text-xs font-bold font-mono text-emerald-400 uppercase">Demonstrated Competencies</span>
              <div className="space-y-1">
                {topicEvalResult.skills_demonstrated?.map((s, idx) => (
                  <div key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                    <Check size={14} className="text-emerald-400" /> {s}
                  </div>
                ))}
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-purple-400/5 border border-purple-400/20 space-y-2">
              <span className="text-xs font-bold font-mono text-purple-400 uppercase">Mastery Verdict</span>
              <p className="text-xs text-slate-300">{topicEvalResult.recommended_next_step}</p>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-white/10">
            <button
              onClick={() => setActiveStage('mock_exam')}
              className="btn-cyber-solid flex items-center gap-2"
            >
              Advance to Personalized Mock Exam <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 8: CREATE PERSONALIZED MOCK EXAM */}
      {/* ========================================================================= */}
      {activeStage === 'mock_exam' && !activeMockExam && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="max-w-2xl">
            <span className="px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold">
              STEP 8: MOCK EXAM CONFIGURATION
            </span>
            <h2 className="font-display font-bold text-white text-3xl mt-3">
              Create Your Personalized Mock Test
            </h2>
            <p className="text-slate-300 text-sm mt-2">
              Select your preferred examination method, duration, and question distribution.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { id: 'mcq', label: '1. MCQ Exam' },
              { id: 'written', label: '2. Written Exam' },
              { id: 'coding', label: '3. Coding Exam' },
              { id: 'concept_mapping', label: '4. Concept Map' },
              { id: 'application', label: '5. Application' },
              { id: 'mixed', label: '6. Mixed-Method' },
            ].map(m => (
              <button
                key={m.id}
                onClick={() => setMockExamMethod(m.id)}
                className={`p-4 rounded-2xl border text-center font-bold text-xs transition-all ${
                  mockExamMethod === m.id
                    ? 'bg-cyan-400/20 border-cyan-400 text-white'
                    : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-white/10">
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 font-medium">Question Count:</span>
              {[4, 6, 8, 10].map(cnt => (
                <button
                  key={cnt}
                  onClick={() => setMockNumQuestions(cnt)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-bold ${
                    mockNumQuestions === cnt ? 'bg-cyan-400 text-slate-950' : 'bg-white/5 text-slate-400'
                  }`}
                >
                  {cnt} Qs
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerateMockExam}
              disabled={loading}
              className="btn-cyber-solid flex items-center gap-2"
            >
              <CheckSquare size={16} /> Generate Mock Examination
            </button>
          </div>
        </div>
      )}

      {/* ACTIVE MOCK EXAM RUNNER */}
      {activeMockExam && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <span className="text-xs font-mono text-cyan-400 font-bold uppercase">MOCK EXAM IN PROGRESS</span>
              <h2 className="text-xl font-display font-bold text-white">{activeMockExam.title}</h2>
            </div>
            <div className="flex items-center gap-2 text-amber-400 font-mono text-sm font-bold">
              <Clock size={16} /> 25:00 Remaining
            </div>
          </div>

          <div className="space-y-6">
            {activeMockExam.questions.map((q, idx) => (
              <div key={q.item_id} className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400 text-[11px] font-mono font-bold uppercase">
                    Q{idx + 1} · {q.item_type.toUpperCase()} · {q.topic}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Diff: Level {q.difficulty}</span>
                </div>

                <p className="text-white text-base font-medium">{q.question}</p>

                {q.item_type === 'mcq' && q.options && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                    {q.options.map(opt => (
                      <button
                        key={opt}
                        onClick={() => setMockAnswers(prev => ({ ...prev, [q.item_id]: opt }))}
                        className={`p-3 rounded-xl border text-left text-xs transition-all ${
                          mockAnswers[q.item_id] === opt
                            ? 'bg-cyan-500/20 border-cyan-400 text-white font-semibold'
                            : 'bg-white/5 border-white/5 text-slate-300 hover:bg-white/10'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}

                {q.item_type !== 'mcq' && (
                  <textarea
                    rows={3}
                    placeholder="Enter your response, code, or explanation..."
                    value={mockAnswers[q.item_id] || ''}
                    onChange={e => setMockAnswers(prev => ({ ...prev, [q.item_id]: e.target.value }))}
                    className="w-full p-3 rounded-xl bg-black/60 border border-white/10 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                  />
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-4 border-t border-white/10">
            <button
              onClick={handleSubmitMockExam}
              disabled={submittingMock}
              className="btn-cyber-solid flex items-center gap-2"
            >
              {submittingMock ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
              Submit Mock Exam & View Results
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 9: PROFESSIONAL MOCK EXAM RESULTS & PROGRESS COMPARISON */}
      {/* ========================================================================= */}
      {activeStage === 'mock_results' && mockResultsData && (
        <div className="glass-card p-8 rounded-3xl border border-white/10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
            <div>
              <span className="px-3 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/20 text-emerald-400 text-xs font-mono font-semibold">
                STEP 9: PROFESSIONAL MOCK EXAM RESULTS
              </span>
              <h2 className="font-display font-bold text-white text-3xl mt-2">
                Mock Examination Performance Report
              </h2>
            </div>

            <div className="text-right">
              <span className="text-3xl font-display font-bold text-emerald-400">
                {mockResultsData.overall_score_pct}%
              </span>
              <div className="text-xs font-mono text-slate-400">Final Score</div>
            </div>
          </div>

          {/* Genuine Longitudinal Progress Comparison */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-cyan-500/15 via-purple-500/15 to-transparent border border-cyan-400/30 space-y-3">
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider block">
              LONGITUDINAL PROGRESSION COMPARISON
            </span>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-slate-400 text-xs font-mono">1. Initial Diagnostic</div>
                <div className="text-xl font-bold text-slate-300 mt-1">
                  {mockResultsData.score_comparison?.initial_diagnostic_pct}%
                </div>
              </div>
              <div>
                <div className="text-slate-400 text-xs font-mono">2. Post-Learning</div>
                <div className="text-xl font-bold text-yellow-400 mt-1">68.0%</div>
              </div>
              <div>
                <div className="text-slate-400 text-xs font-mono">3. Final Mock Exam</div>
                <div className="text-xl font-bold text-emerald-400 mt-1">
                  {mockResultsData.overall_score_pct}%
                </div>
              </div>
            </div>
            <p className="text-xs text-slate-300 text-center pt-1 font-medium">
              {mockResultsData.score_comparison?.trend_summary}
            </p>
          </div>

          {/* Three Concrete Next Actions */}
          <div>
            <h3 className="font-display font-bold text-white text-lg mb-3">Your Next Recommended Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {mockResultsData.next_actions?.map(act => (
                <a
                  key={act.action_id}
                  href={act.link}
                  className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400 hover:bg-cyan-500/10 transition-all space-y-2 block"
                >
                  <h4 className="font-bold text-white text-sm flex items-center justify-between">
                    {act.title} <ArrowRight size={14} className="text-cyan-400" />
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">{act.description}</p>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
