import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Brain, Play, RotateCcw, Award, AlertCircle, CheckCircle2, XCircle,
  HelpCircle, ArrowRight, Calendar, Clock, BookOpen, Sparkles, X,
  ChevronRight, RefreshCw, Zap, ShieldAlert, Check, TrendingUp,
  Cpu, Activity, Layers, Compass, BarChart3, Database, Eye,
  ChevronLeft, Timer, ListChecks, ArrowUpRight
} from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function TutorPage({ forcedMode }) {
  const [searchParams] = useSearchParams();
  const initialMode = forcedMode || searchParams.get('mode');

  // Top-level tab: 'workflows' | 'research_lab'
  const [activeTab, setActiveTab] = useState('workflows');

  // Active workflow state
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [inlineNotice, setInlineNotice] = useState(null); // { type: 'error'|'info'|'success', message: '', actionLabel: '', onAction: fn }

  // Active practice interaction state
  const [currentAction, setCurrentAction] = useState(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [submittingStep, setSubmittingStep] = useState(false);
  const [stepFeedback, setStepFeedback] = useState(null);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [sessionSummary, setSessionSummary] = useState({ questions_answered: 0, questions_correct: 0 });

  // Assistance modal states (Explain, Worked Example, Prerequisites)
  const [assistanceType, setAssistanceType] = useState(null); // 'explain' | 'worked_example' | 'prerequisites' | null
  const [assistanceData, setAssistanceData] = useState(null);
  const [assistanceLoading, setAssistanceLoading] = useState(false);

  // Workflow C: Timed Mock Exam State
  const [mockExamSession, setMockExamSession] = useState(null);
  const [mockCurrentIdx, setMockCurrentIdx] = useState(0);
  const [mockAnswers, setMockAnswers] = useState({});
  const [mockTimeRemaining, setMockTimeRemaining] = useState(900); // 15 mins in sec
  const [mockSubmitting, setMockSubmitting] = useState(false);
  const [mockResult, setMockResult] = useState(null);
  const timerRef = useRef(null);

  // Workflow D: Spaced Retrieval Flashcard State
  const [flashcardFlipped, setFlashcardFlipped] = useState(false);
  const [spacedSubmitting, setSpacedSubmitting] = useState(false);
  const [spacedFeedback, setSpacedFeedback] = useState(null);

  // Exam configuration modal state
  const [showExamSetup, setShowExamSetup] = useState(false);
  const [examForm, setExamForm] = useState({
    name: 'Upcoming AI/ML Semester Exam',
    date: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10),
    minutes: 45,
    selectedTopics: ['python', 'probability', 'linear regression', 'classification', 'neural networks'],
    targetScore: 85,
  });

  // Research Lab state
  const [researchData, setResearchData] = useState(null);
  const [researchLoading, setResearchLoading] = useState(false);

  const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';

  const ALL_TOPICS = [
    'python', 'probability', 'statistics', 'data preprocessing',
    'linear regression', 'classification', 'decision trees', 'clustering',
    'svm', 'ensemble methods', 'neural networks', 'nlp', 'transformers',
    'rag', 'llm', 'reinforcement learning', 'automl'
  ];

  // Restore session from sessionStorage or launch via URL parameter on mount
  useEffect(() => {
    if (initialMode && ['continue', 'weak_topics', 'exam_prep', 'revision'].includes(initialMode)) {
      startWorkflow(initialMode);
    } else {
      // Check for saved session
      try {
        const saved = sessionStorage.getItem('autolearn_active_session');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.session_id) {
            restoreSession(parsed.session_id);
          }
        }
      } catch (e) {
        sessionStorage.removeItem('autolearn_active_session');
      }
    }
  }, [initialMode]);

  // Load research lab data when tab changes to research_lab
  useEffect(() => {
    if (activeTab === 'research_lab') {
      fetchResearchLabData();
    }
  }, [activeTab]);

  // Mock Exam Timer interval
  useEffect(() => {
    if (mockExamSession && !mockResult) {
      timerRef.current = setInterval(() => {
        setMockTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            handleAutoSubmitMock();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [mockExamSession, mockResult]);

  const restoreSession = async (sessionId) => {
    try {
      const res = await apiFetch(`/api/workflow/session/${sessionId}`);
      if (res && res.ok && res.session) {
        const s = res.session;
        // Resume into workflow
        startWorkflow(s.workflow_type?.replace('workflow_', '') || 'continue');
      } else {
        sessionStorage.removeItem('autolearn_active_session');
      }
    } catch {
      sessionStorage.removeItem('autolearn_active_session');
    }
  };

  const fetchResearchLabData = async () => {
    setResearchLoading(true);
    try {
      const res = await apiFetch(`/api/rl/research-lab/${learnerId}`);
      if (res && res.ok) {
        setResearchData(res);
      }
    } catch (err) {
      console.error('Failed to load RL telemetry:', err);
    } finally {
      setResearchLoading(false);
    }
  };

  // Launch one of the 4 distinct workflows
  const startWorkflow = async (mode) => {
    setWorkflowLoading(true);
    setInlineNotice(null);
    setStepFeedback(null);
    setSelectedOption('');
    setAssistanceType(null);
    setAssistanceData(null);
    setMockExamSession(null);
    setMockResult(null);
    setFlashcardFlipped(false);
    setSpacedFeedback(null);

    let endpoint = '';
    if (mode === 'continue') endpoint = `/api/workflow/continue/${learnerId}`;
    else if (mode === 'weak_topics') endpoint = `/api/workflow/weak-topics/${learnerId}`;
    else if (mode === 'exam_prep') endpoint = `/api/workflow/exam-prep/${learnerId}`;
    else if (mode === 'revision') endpoint = `/api/workflow/revision/${learnerId}`;

    try {
      const res = await apiFetch(endpoint);
      if (res && res.ok) {
        if (res.needs_setup && mode === 'exam_prep') {
          setShowExamSetup(true);
          setWorkflowLoading(false);
          return;
        }

        setActiveWorkflow(res);
        setCurrentAction(res.selected_action);
        setQuestionStartTime(Date.now());
        setSessionSummary({ questions_answered: 0, questions_correct: 0 });

        // Save session in sessionStorage for seamless refresh survival
        if (res.session_id) {
          sessionStorage.setItem('autolearn_active_session', JSON.stringify({
            session_id: res.session_id,
            workflow_type: res.workflow_type,
          }));
        }
      } else {
        throw new Error(res?.error || 'Unable to launch learning workflow.');
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Workflow launch failed.',
        actionLabel: 'Retry',
        onAction: () => startWorkflow(mode),
      });
    } finally {
      setWorkflowLoading(false);
    }
  };

  // Configure Exam Roadmap
  const handleConfigureExamPlan = async (e) => {
    e.preventDefault();
    setWorkflowLoading(true);
    try {
      const res = await apiFetch('/api/workflow/exam-prep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          exam_date: examForm.date,
          daily_minutes: examForm.minutes,
          syllabus_topics: examForm.selectedTopics,
          target_score_pct: examForm.targetScore,
        }),
      });

      if (res && res.ok) {
        setShowExamSetup(false);
        setActiveWorkflow(res);
        setCurrentAction(res.selected_action);
        setQuestionStartTime(Date.now());
        setSessionSummary({ questions_answered: 0, questions_correct: 0 });
        if (res.session_id) {
          sessionStorage.setItem('autolearn_active_session', JSON.stringify({
            session_id: res.session_id,
            workflow_type: res.workflow_type,
          }));
        }
      } else {
        setInlineNotice({
          type: 'error',
          message: res?.error || 'Failed to configure exam plan.',
        });
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Exam configuration failed.',
      });
    } finally {
      setWorkflowLoading(false);
    }
  };

  // Start Timed Mock Exam Simulation (Workflow C)
  const handleStartMockExam = async () => {
    setWorkflowLoading(true);
    try {
      const res = await apiFetch('/api/workflow/mock-exam/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          plan_id: activeWorkflow?.exam_plan?.plan_id,
          num_questions: 5,
          syllabus_topics: activeWorkflow?.exam_plan?.syllabus_topics,
        }),
      });

      if (res && res.ok) {
        setMockExamSession(res);
        setMockCurrentIdx(0);
        setMockAnswers({});
        setMockTimeRemaining(15 * 60);
        setMockResult(null);
      } else {
        setInlineNotice({
          type: 'error',
          message: res?.error || 'Failed to initialize mock exam.',
        });
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Mock exam startup failed.',
      });
    } finally {
      setWorkflowLoading(false);
    }
  };

  // Auto-submit mock exam when timer expires
  const handleAutoSubmitMock = () => {
    handleSubmitMockExam();
  };

  // Submit Mock Exam
  const handleSubmitMockExam = async () => {
    if (!mockExamSession || mockSubmitting) return;
    setMockSubmitting(true);
    clearInterval(timerRef.current);

    try {
      const res = await apiFetch('/api/workflow/mock-exam/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: mockExamSession.session_id,
          answers: mockAnswers,
        }),
      });

      if (res && res.ok) {
        setMockResult(res);
      } else {
        setInlineNotice({
          type: 'error',
          message: res?.error || 'Failed to score mock exam.',
        });
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Error submitting mock exam.',
      });
    } finally {
      setMockSubmitting(false);
    }
  };

  // Submit Spaced Retrieval Flashcard Rating (Workflow D)
  const handleRateFlashcard = async (rating) => {
    if (!activeWorkflow || !activeQuestion) return;
    setSpacedSubmitting(true);

    try {
      const res = await apiFetch('/api/workflow/spaced-review/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeWorkflow.session_id,
          item_id: activeQuestion.item_id,
          recall_rating: rating,
        }),
      });

      if (res && res.ok) {
        setSpacedFeedback(res);
        setSessionSummary(prev => ({
          questions_answered: prev.questions_answered + 1,
          questions_correct: prev.questions_correct + (rating !== 'lapse' ? 1 : 0),
        }));
      } else {
        setInlineNotice({
          type: 'error',
          message: res?.error || 'Failed to record spaced review.',
        });
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Error saving review.',
      });
    } finally {
      setSpacedSubmitting(false);
    }
  };

  // Next Flashcard in Workflow D
  const handleNextFlashcard = () => {
    setFlashcardFlipped(false);
    setSpacedFeedback(null);
    startWorkflow('revision');
  };

  // Submit Practice Exercise Answer
  const handleAnswerSubmit = async () => {
    if (!activeWorkflow || !currentAction) return;

    const questionObj = currentAction.question || currentAction.practice_question;
    if (!questionObj || !selectedOption) return;

    setSubmittingStep(true);
    const elapsed = Date.now() - questionStartTime;

    try {
      const res = await apiFetch('/api/workflow/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_type: activeWorkflow.workflow_type,
          session_id: activeWorkflow.session_id,
          item_id: questionObj.item_id,
          selected_option: selectedOption,
          response_time_ms: Math.max(elapsed, 500),
        }),
      });

      if (res && res.ok) {
        setStepFeedback(res.feedback);
        setSessionSummary(prev => ({
          questions_answered: prev.questions_answered + 1,
          questions_correct: prev.questions_correct + (res.feedback.is_correct ? 1 : 0),
        }));
        if (res.next_action) {
          setActiveWorkflow(prev => ({
            ...prev,
            stagedNextAction: res.next_action,
          }));
        }
      } else {
        // If session was completed or expired, show friendly inline recovery
        if (res?.status === 'EXPIRED' || res?.status === 'COMPLETED' || res?.status === 'NOT_FOUND') {
          setInlineNotice({
            type: 'info',
            message: res.error,
            actionLabel: 'Resume Fresh Session',
            onAction: () => startWorkflow(activeWorkflow.workflow_type.replace('workflow_', '')),
          });
        } else {
          throw new Error(res?.error || 'Failed to evaluate response.');
        }
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: err.message || 'Error submitting response.',
        actionLabel: 'Retry',
        onAction: handleAnswerSubmit,
      });
    } finally {
      setSubmittingStep(false);
    }
  };

  // Advance to next staged question
  const handleAdvanceToNext = () => {
    if (activeWorkflow && activeWorkflow.stagedNextAction) {
      setCurrentAction(activeWorkflow.stagedNextAction);
      setActiveWorkflow(prev => ({ ...prev, stagedNextAction: null }));
      setSelectedOption('');
      setStepFeedback(null);
      setAssistanceType(null);
      setAssistanceData(null);
      setQuestionStartTime(Date.now());
    }
  };

  // Unified Assistance Dispatcher (Explain, Worked Example, Easier Step, Prerequisites)
  const requestAssistance = async (action) => {
    if (!activeWorkflow) return;
    setAssistanceLoading(true);
    setInlineNotice(null);

    const questionObj = currentAction?.question || currentAction?.practice_question;
    const currentTopic = activeWorkflow.current_topic || questionObj?.topic || 'python';

    try {
      const res = await apiFetch('/api/workflow/assistance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeWorkflow.session_id,
          action: action,
          item_id: questionObj?.item_id,
          topic: currentTopic,
          learner_id: learnerId,
          selected_option: selectedOption || null,
        }),
      });

      if (res && res.ok) {
        if (action === 'easier_step' && res.question) {
          // Switch active question smoothly to easier exercise
          setCurrentAction({
            action_type: 'easier_question',
            question: res.question,
            target_topic: res.topic,
            rationale: res.rationale || 'Switched to a guided foundational exercise (Level 1-2) to build conceptual confidence.'
          });
          setSelectedOption('');
          setStepFeedback(null);
          setQuestionStartTime(Date.now());
          setAssistanceType(null);
          setAssistanceData(null);
        } else {
          setAssistanceType(action);
          setAssistanceData(res);
        }
      } else {
        // Handle session expired/completed without alert()
        if (res?.status === 'EXPIRED' || res?.status === 'COMPLETED' || res?.status === 'NOT_FOUND') {
          setInlineNotice({
            type: 'info',
            message: res.error,
            actionLabel: 'Start New Session',
            onAction: () => startWorkflow('continue'),
          });
        } else {
          setInlineNotice({
            type: 'error',
            message: res?.error || 'Help feature currently unavailable.',
            actionLabel: 'Retry',
            onAction: () => requestAssistance(action),
          });
        }
      }
    } catch (err) {
      setInlineNotice({
        type: 'error',
        message: 'Assistance request failed: ' + err.message,
        actionLabel: 'Retry',
        onAction: () => requestAssistance(action),
      });
    } finally {
      setAssistanceLoading(false);
    }
  };

  const endSession = () => {
    sessionStorage.removeItem('autolearn_active_session');
    setActiveWorkflow(null);
    setCurrentAction(null);
    setSelectedOption('');
    setStepFeedback(null);
    setAssistanceType(null);
    setAssistanceData(null);
    setMockExamSession(null);
    setMockResult(null);
  };

  const toggleTopic = (t) => {
    setExamForm(prev => {
      const exists = prev.selectedTopics.includes(t);
      return {
        ...prev,
        selectedTopics: exists
          ? prev.selectedTopics.filter(x => x !== t)
          : [...prev.selectedTopics, t],
      };
    });
  };

  const activeQuestion = currentAction?.question || currentAction?.practice_question;

  // Format timer MM:SS
  const formatTimer = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header & Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider">
              Autonomous Adaptive Learning
            </span>
          </div>
          <h1 className="font-display font-bold text-2xl lg:text-3xl text-white">
            AutoLearn Personalized Tutor
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Top-Level Tab Switcher */}
          <div className="p-1 rounded-xl bg-white/5 border border-white/10 flex items-center gap-1 text-xs">
            <button
              onClick={() => setActiveTab('workflows')}
              className={`px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 ${
                activeTab === 'workflows'
                  ? 'bg-cyan-400/20 text-cyan-300 border border-cyan-400/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Compass size={14} />
              <span>4 Learning Modules</span>
            </button>
            <button
              onClick={() => setActiveTab('research_lab')}
              className={`px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 ${
                activeTab === 'research_lab'
                  ? 'bg-purple-400/20 text-purple-300 border border-purple-400/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Cpu size={14} />
              <span>RL Research Lab</span>
            </button>
          </div>

          {(activeWorkflow || mockExamSession) && (
            <button
              onClick={endSession}
              className="btn-cyber text-xs py-1.5 px-3 border-red-400/40 text-red-300 hover:border-red-400 flex items-center gap-1.5"
            >
              <X size={14} />
              Exit Module
            </button>
          )}
        </div>
      </div>

      {/* Inline Notification Banner (Replaces browser alert) */}
      {inlineNotice && (
        <div className={`p-4 rounded-xl border text-xs flex items-center justify-between gap-3 ${
          inlineNotice.type === 'error'
            ? 'bg-red-400/10 border-red-400/30 text-red-300'
            : inlineNotice.type === 'success'
            ? 'bg-green-400/10 border-green-400/30 text-green-300'
            : 'bg-cyan-400/10 border-cyan-400/30 text-cyan-300'
        }`}>
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="flex-shrink-0" />
            <span>{inlineNotice.message}</span>
          </div>
          <div className="flex items-center gap-2">
            {inlineNotice.onAction && (
              <button
                onClick={inlineNotice.onAction}
                className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 font-medium text-white transition text-[11px]"
              >
                {inlineNotice.actionLabel || 'Action'}
              </button>
            )}
            <button
              onClick={() => setInlineNotice(null)}
              className="text-slate-400 hover:text-white"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW A: RL RESEARCH LAB & TRANSPARENCY TAB
         ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'research_lab' && (
        <div className="space-y-6">
          <div className="glass-card p-6 border-purple-400/30 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <Cpu size={20} className="text-purple-400" />
                <h2 className="font-display font-bold text-lg text-white">Reinforcement Learning Transparency & Diagnostics</h2>
              </div>
              <button
                onClick={fetchResearchLabData}
                disabled={researchLoading}
                className="btn-cyber text-xs py-1 px-2.5 flex items-center gap-1"
              >
                <RefreshCw size={12} className={researchLoading ? 'animate-spin' : ''} />
                Refresh Telemetry
              </button>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Real-world educational safety invariant: live student exercise selection is powered by the production
              Composite Adaptive Policy with prerequisite action masks and difficulty hysteresis safeguards.
              Experimental Deep RL policies (Dueling Double DQN) and Contextual Bandit baselines (LinUCB) operate in
              controlled research evaluation mode.
            </p>

            {/* Policy Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              {/* Production Policy */}
              <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold">Active Production</span>
                  <span className="badge-chip text-[10px] text-green-400 bg-green-400/10 border border-green-400/30">ONLINE</span>
                </div>
                <h4 className="font-display font-semibold text-white text-sm">Composite Adaptive Policy</h4>
                <p className="text-slate-400 text-xs">
                  Combines BKT posterior mastery, topological prerequisite masks, and hysteresis difficulty step-up/down.
                </p>
              </div>

              {/* Experimental DQN */}
              <div className="p-4 rounded-xl bg-purple-400/5 border border-purple-400/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-bold">Deep RL Research</span>
                  <span className="badge-chip text-[10px] text-yellow-300 bg-yellow-400/10 border border-yellow-400/30">EXPERIMENTAL</span>
                </div>
                <h4 className="font-display font-semibold text-white text-sm">Dueling Double DQN</h4>
                <p className="text-slate-400 text-xs">
                  99-dim observation space, Discrete(52) action space. Checkpoint: <code className="text-purple-300 font-mono text-[10px]">models/dqn/dueling_dqn_final.pt</code>.
                </p>
              </div>

              {/* Contextual Bandit */}
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">Contextual Bandit</span>
                  <span className="badge-chip text-[10px] text-slate-300 bg-white/10 border border-white/20">RESEARCH BASELINE</span>
                </div>
                <h4 className="font-display font-semibold text-white text-sm">LinUCB Exploration</h4>
                <p className="text-slate-400 text-xs">
                  Upper Confidence Bound arm selection over BKT uncertainty, attempt recency, and difficulty alignment.
                </p>
              </div>
            </div>
          </div>

          {/* 10-Policy Comparative Benchmark Table */}
          {researchData && researchData.policy_comparison_benchmark && (
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display font-bold text-white text-base">10-Policy Evaluation Benchmark</h3>
                  <p className="text-slate-400 text-xs">200 simulated evaluation episodes across 4 synthetic learner archetypes</p>
                </div>
                <span className="text-xs font-mono text-cyan-400">reports/phase7_policy_comparison.json</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-slate-300 border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-500 font-semibold text-left">
                      <th className="py-2.5 px-3">Policy</th>
                      <th className="py-2.5 px-3">Mean Reward</th>
                      <th className="py-2.5 px-3">Reward 95% CI</th>
                      <th className="py-2.5 px-3">Accuracy</th>
                      <th className="py-2.5 px-3">Net Mastery Gain</th>
                      <th className="py-2.5 px-3">BKT MAE</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {researchData.policy_comparison_benchmark.map((row) => (
                      <tr key={row.policy_id} className={`border-b border-white/5 hover:bg-white/5 ${row.is_production ? 'bg-cyan-400/5' : ''}`}>
                        <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-1.5">
                          {row.is_production && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />}
                          <span>{row.policy_name}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-cyan-300">{row.mean_reward}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-400">±{row.reward_ci95}</td>
                        <td className="py-2.5 px-3 font-mono text-white">{row.accuracy_pct}%</td>
                        <td className="py-2.5 px-3 font-mono text-green-400">{row.net_mastery_gain}</td>
                        <td className="py-2.5 px-3 font-mono text-purple-300">{row.bkt_mae}</td>
                        <td className="py-2.5 px-3">
                          {row.is_production ? (
                            <span className="badge-chip text-[10px] text-cyan-300 bg-cyan-400/15 border border-cyan-400/30">Active Production</span>
                          ) : row.is_experimental ? (
                            <span className="badge-chip text-[10px] text-yellow-300 bg-yellow-400/15 border border-yellow-400/30">Experimental</span>
                          ) : (
                            <span className="badge-chip text-[10px] text-slate-400 bg-white/5 border border-white/10">Research Baseline</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Diagnostic Information Gain Section */}
          {researchData && researchData.diagnostic_entropy_sampling && (
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-2">
                <Brain size={18} className="text-cyan-400" />
                <h3 className="font-display font-bold text-white text-base">Diagnostic Information Gain (Entropy Reduction)</h3>
              </div>
              <p className="text-slate-400 text-xs">
                Expected entropy reduction E[ΔH] indicates which skills provide maximum diagnostic value when tested.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {researchData.diagnostic_entropy_sampling.map(sample => (
                  <div key={sample.topic} className="p-3 rounded-xl bg-white/4 border border-white/8 space-y-1">
                    <div className="text-[11px] text-slate-300 font-medium capitalize truncate">{sample.topic.replace(/_/g, ' ')}</div>
                    <div className="text-[10px] text-slate-500">Prior: {sample.prior_mastery}</div>
                    <div className="font-mono text-cyan-400 font-bold text-xs">+{sample.expected_information_gain_bits} bits</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW B: 4 MODULE ENTRY CARDS (When no active workflow)
         ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'workflows' && !activeWorkflow && !mockExamSession && (
        <div className="space-y-6">
          <div className="glass-card p-6 border-cyan-400/20">
            <h2 className="font-display font-bold text-lg text-white mb-1">Choose a Personalized Learning Strategy</h2>
            <p className="text-slate-400 text-xs">
              Select one of the four purpose-built workflows below. Each executes an isolated backend algorithm.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 1. Continue Learning */}
            <div className="glass-card p-6 border-cyan-400/30 flex flex-col justify-between space-y-4 hover:border-cyan-400/50 transition">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-cyan-400/10 flex items-center justify-center text-cyan-400">
                    <Play size={20} />
                  </div>
                  <span className="badge-chip text-[10px] text-cyan-300 bg-cyan-400/15 border border-cyan-400/30">Workflow A</span>
                </div>
                <h3 className="font-display font-bold text-lg text-white">Continue Learning</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Resume your curriculum journey right where you left off. The DAG topological planner identifies your next prerequisite-eligible concept.
                </p>
              </div>
              <button
                onClick={() => startWorkflow('continue')}
                disabled={workflowLoading}
                className="btn-cyber text-xs py-2.5 px-4 w-full flex items-center justify-center gap-2"
              >
                {workflowLoading ? <RefreshCw size={14} className="animate-spin" /> : null}
                Resume Curriculum Path <ArrowRight size={14} />
              </button>
            </div>

            {/* 2. Improve My Weak Topics */}
            <div className="glass-card p-6 border-red-400/30 flex flex-col justify-between space-y-4 hover:border-red-400/50 transition">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-red-400/10 flex items-center justify-center text-red-400">
                    <Zap size={20} />
                  </div>
                  <span className="badge-chip text-[10px] text-red-300 bg-red-400/15 border border-red-400/30">Workflow B</span>
                </div>
                <h3 className="font-display font-bold text-lg text-white">Improve My Weak Topics</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Targeted practice focused on concepts where your accuracy or understanding is lowest. Automatically detects and repairs prerequisite gaps.
                </p>
              </div>
              <button
                onClick={() => startWorkflow('weak_topics')}
                disabled={workflowLoading}
                className="btn-cyber text-xs py-2.5 px-4 w-full flex items-center justify-center gap-2 border-red-400/40 text-red-300 hover:border-red-400"
              >
                {workflowLoading ? <RefreshCw size={14} className="animate-spin" /> : null}
                Strengthen Weak Concepts <ArrowRight size={14} />
              </button>
            </div>

            {/* 3. Prepare for an Exam */}
            <div className="glass-card p-6 border-purple-400/30 flex flex-col justify-between space-y-4 hover:border-purple-400/50 transition">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-purple-400/10 flex items-center justify-center text-purple-400">
                    <Calendar size={20} />
                  </div>
                  <span className="badge-chip text-[10px] text-purple-300 bg-purple-400/15 border border-purple-400/30">Workflow C</span>
                </div>
                <h3 className="font-display font-bold text-lg text-white">Prepare for an Exam</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Follow a day-by-day study roadmap leading up to your exam date, with dynamic schedule rebalancing and full mock exams.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => startWorkflow('exam_prep')}
                  disabled={workflowLoading}
                  className="btn-cyber text-xs py-2.5 px-3 flex items-center justify-center gap-1.5 bg-purple-400/20 border-purple-400 text-purple-200"
                >
                  {workflowLoading ? <RefreshCw size={12} className="animate-spin" /> : null}
                  Start Exam Practice <ArrowRight size={12} />
                </button>
                <button
                  onClick={() => setShowExamSetup(true)}
                  className="btn-cyber text-xs py-2.5 px-3 text-slate-300"
                >
                  Configure Plan
                </button>
              </div>
            </div>

            {/* 4. Revise Previous Topics */}
            <div className="glass-card p-6 border-emerald-400/30 flex flex-col justify-between space-y-4 hover:border-emerald-400/50 transition">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-emerald-400/10 flex items-center justify-center text-emerald-400">
                    <RotateCcw size={20} />
                  </div>
                  <span className="badge-chip text-[10px] text-emerald-300 bg-emerald-400/15 border border-emerald-400/30">Workflow D</span>
                </div>
                <h3 className="font-display font-bold text-lg text-white">Revise Previous Topics</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Memory-aware half-life spaced repetition. Review earlier concepts before retrieval probability decays below retention threshold.
                </p>
              </div>
              <button
                onClick={() => startWorkflow('revision')}
                disabled={workflowLoading}
                className="btn-cyber text-xs py-2.5 px-4 w-full flex items-center justify-center gap-2 border-emerald-400/40 text-emerald-300 hover:border-emerald-400"
              >
                {workflowLoading ? <RefreshCw size={14} className="animate-spin" /> : null}
                Start Memory Review <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW C1: TIMED MOCK EXAM SIMULATION (Dedicated Workflow C Interface)
         ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'workflows' && mockExamSession && (
        <div className="glass-card p-6 space-y-6 border-purple-400/40">
          {!mockResult ? (
            <>
              {/* Mock Exam Top Header with Countdown Timer */}
              <div className="flex items-center justify-between flex-wrap gap-3 border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Timer size={20} className="text-purple-400" />
                    <h2 className="font-display font-bold text-lg text-white">{mockExamSession.exam_title}</h2>
                  </div>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Question {mockCurrentIdx + 1} of {mockExamSession.total_questions} · Timed Exam Condition
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 font-mono text-sm font-bold ${
                    mockTimeRemaining < 180 ? 'bg-red-400/20 border-red-400 text-red-300 animate-pulse' : 'bg-purple-400/15 border-purple-400/40 text-purple-300'
                  }`}>
                    <Clock size={16} />
                    <span>{formatTimer(mockTimeRemaining)}</span>
                  </div>
                  <button
                    onClick={handleSubmitMockExam}
                    disabled={mockSubmitting}
                    className="btn-cyber-solid text-xs py-2 px-4 bg-purple-500 hover:bg-purple-400 border-purple-400"
                  >
                    {mockSubmitting ? 'Scoring...' : 'Submit Exam'}
                  </button>
                </div>
              </div>

              {/* Question Navigation Palette */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                {mockExamSession.questions.map((q, idx) => {
                  const isAnswered = !!mockAnswers[q.item_id];
                  const isCurrent = mockCurrentIdx === idx;
                  return (
                    <button
                      key={q.item_id}
                      onClick={() => setMockCurrentIdx(idx)}
                      className={`w-8 h-8 rounded-lg font-mono text-xs font-bold transition ${
                        isCurrent
                          ? 'bg-purple-500 text-white border border-purple-300'
                          : isAnswered
                          ? 'bg-purple-500/30 text-purple-200 border border-purple-400/40'
                          : 'bg-white/5 text-slate-400 hover:text-white border border-white/10'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              {/* Active Mock Question */}
              {mockExamSession.questions[mockCurrentIdx] && (
                <div className="space-y-4 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="badge-chip text-cyan-300 bg-cyan-400/15 border border-cyan-400/30 capitalize">
                      {mockExamSession.questions[mockCurrentIdx].topic?.replace(/_/g, ' ')}
                    </span>
                    <span className="badge-chip text-slate-400 bg-white/5 border border-white/10">
                      Difficulty {mockExamSession.questions[mockCurrentIdx].difficulty}/5
                    </span>
                  </div>

                  <div className="text-base text-white font-medium leading-relaxed">
                    {mockExamSession.questions[mockCurrentIdx].question}
                  </div>

                  {/* Options */}
                  <div className="space-y-2.5 pt-2">
                    {mockExamSession.questions[mockCurrentIdx].options.map((opt, oIdx) => {
                      const currQId = mockExamSession.questions[mockCurrentIdx].item_id;
                      const isSelected = mockAnswers[currQId] === opt;
                      return (
                        <button
                          key={oIdx}
                          onClick={() => setMockAnswers({ ...mockAnswers, [currQId]: opt })}
                          className={`w-full p-3.5 rounded-xl border text-left text-xs transition flex items-center gap-3 ${
                            isSelected
                              ? 'border-purple-400 bg-purple-400/15 text-white font-medium'
                              : 'glass-card border-white/10 hover:border-purple-400/40 text-slate-200'
                          }`}
                        >
                          <span className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                            isSelected ? 'bg-purple-500 text-white' : 'bg-white/5 text-slate-400'
                          }`}>
                            {String.fromCharCode(65 + oIdx)}
                          </span>
                          <span>{opt}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Mock Navigation Prev/Next */}
                  <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <button
                      onClick={() => setMockCurrentIdx(prev => Math.max(0, prev - 1))}
                      disabled={mockCurrentIdx === 0}
                      className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1 disabled:opacity-30"
                    >
                      <ChevronLeft size={14} /> Previous
                    </button>
                    <button
                      onClick={() => setMockCurrentIdx(prev => Math.min(mockExamSession.total_questions - 1, prev + 1))}
                      disabled={mockCurrentIdx === mockExamSession.total_questions - 1}
                      className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1 disabled:opacity-30"
                    >
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Mock Exam Score Report */
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-center space-y-2">
                <span className={`badge-chip text-xs px-3 py-1 ${
                  mockResult.passed ? 'text-green-300 bg-green-400/20 border-green-400/40' : 'text-red-300 bg-red-400/20 border-red-400/40'
                }`}>
                  {mockResult.passed ? 'PASSED MOCK EXAM' : 'NEEDS ADDITIONAL PREPARATION'}
                </span>
                <h3 className="font-display font-bold text-2xl text-white">
                  Score: {mockResult.score} / {mockResult.total_questions} ({mockResult.score_pct}%)
                </h3>
                <p className="text-slate-300 text-xs max-w-md mx-auto">
                  {mockResult.readiness_summary}
                </p>
              </div>

              {/* Per-Topic Breakdown */}
              <div className="space-y-2">
                <h4 className="font-display font-semibold text-white text-sm">Topic Diagnostic Breakdown</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {Object.entries(mockResult.topic_breakdown || {}).map(([top, stat]) => (
                    <div key={top} className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs space-y-1">
                      <div className="capitalize font-medium text-slate-200">{top.replace(/_/g, ' ')}</div>
                      <div className="font-mono text-cyan-400 font-bold">
                        {stat.correct} / {stat.total} ({Math.round((stat.correct / stat.total) * 100)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
                <button
                  onClick={() => setMockExamSession(null)}
                  className="btn-cyber text-xs py-2 px-4"
                >
                  Return to Study Plan
                </button>
                <button
                  onClick={handleStartMockExam}
                  className="btn-cyber-solid text-xs py-2 px-5 bg-purple-500 border-purple-400"
                >
                  Take Another Mock
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW C2: WORKFLOW D RETRIEVAL FLASHCARD INTERFACE
         ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'workflows' && activeWorkflow?.workflow_type === 'revise_previous_topics' && activeQuestion && !mockExamSession && (
        <div className="space-y-6">
          {/* Spaced Repetition Memory Meter Banner */}
          <div className="glass-card p-6 border-emerald-400/30 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <RotateCcw size={18} className="text-emerald-400" />
                <span className="font-display font-bold text-white text-base">Spaced Repetition Memory Retrieval</span>
              </div>
              <span className="text-xs font-mono text-emerald-300 font-bold">
                Target Recall Strength: {activeWorkflow.retention_estimate_pct}%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-emerald-400/10 border border-emerald-400/30">
                <span className="text-emerald-300 text-[10px] block">Stability (Half-Life):</span>
                <span className="font-mono text-white font-bold">{activeWorkflow.stability_intervals} intervals</span>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <span className="text-slate-400 text-[10px] block">Projection on Success:</span>
                <span className="font-mono text-green-300 font-bold">Expands to {activeWorkflow.expected_interval_on_success} intervals</span>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <span className="text-slate-400 text-[10px] block">Projection on Lapse:</span>
                <span className="font-mono text-yellow-300 font-bold">Resets to {activeWorkflow.expected_interval_on_lapse} interval</span>
              </div>
            </div>
          </div>

          {/* Interactive Retrieval Flashcard Card */}
          <div className="glass-card p-6 space-y-5 border-emerald-400/40">
            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-white/10 pb-3">
              <span className="badge-chip text-xs text-emerald-300 bg-emerald-400/15 border border-emerald-400/30 capitalize">
                {activeQuestion.topic?.replace(/_/g, ' ')}
              </span>
              <span className="text-xs font-mono text-slate-500">{activeQuestion.item_id}</span>
            </div>

            {/* Flashcard Front: Challenge */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-white font-medium text-base leading-relaxed">
              {activeQuestion.question}
            </div>

            {/* Flip / Show Answer Action */}
            {!flashcardFlipped ? (
              <div className="text-center py-4">
                <button
                  onClick={() => setFlashcardFlipped(true)}
                  className="btn-cyber-solid text-xs py-2.5 px-6 bg-emerald-500 hover:bg-emerald-400 border-emerald-400 flex items-center gap-2 mx-auto"
                >
                  <Eye size={15} />
                  Reveal Answer & Memory Rationale
                </button>
              </div>
            ) : (
              /* Flashcard Back: Solution & Self-Rating */
              <div className="space-y-4 pt-2 border-t border-white/10">
                <div className="p-4 rounded-xl bg-emerald-400/10 border border-emerald-400/30 space-y-2">
                  <div className="text-xs font-semibold text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 size={16} />
                    <span>Correct Concept Answer:</span>
                  </div>
                  <div className="text-sm font-bold text-white">
                    {activeQuestion.answer || activeQuestion.options?.[0]}
                  </div>
                  {activeQuestion.explanation && (
                    <p className="text-xs text-slate-300 leading-relaxed pt-1">
                      {activeQuestion.explanation}
                    </p>
                  )}
                </div>

                {/* Spaced Review Self-Rating Buttons */}
                {!spacedFeedback ? (
                  <div className="space-y-2 pt-2">
                    <span className="text-slate-400 text-xs block text-center font-medium">
                      How easily did you retrieve this concept?
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <button
                        onClick={() => handleRateFlashcard('lapse')}
                        disabled={spacedSubmitting}
                        className="p-3 rounded-xl border border-red-400/40 bg-red-400/10 hover:bg-red-400/20 text-red-300 text-xs font-semibold text-center transition"
                      >
                        <span className="block text-sm">🔴 Forgotten</span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">Reset to 1d</span>
                      </button>
                      <button
                        onClick={() => handleRateFlashcard('hard')}
                        disabled={spacedSubmitting}
                        className="p-3 rounded-xl border border-yellow-400/40 bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-300 text-xs font-semibold text-center transition"
                      >
                        <span className="block text-sm">🟡 Hard</span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">Keep interval</span>
                      </button>
                      <button
                        onClick={() => handleRateFlashcard('good')}
                        disabled={spacedSubmitting}
                        className="p-3 rounded-xl border border-green-400/40 bg-green-400/10 hover:bg-green-400/20 text-green-300 text-xs font-semibold text-center transition"
                      >
                        <span className="block text-sm">🟢 Good</span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">Expand 2x</span>
                      </button>
                      <button
                        onClick={() => handleRateFlashcard('easy')}
                        disabled={spacedSubmitting}
                        className="p-3 rounded-xl border border-cyan-400/40 bg-cyan-400/10 hover:bg-cyan-400/20 text-cyan-300 text-xs font-semibold text-center transition"
                      >
                        <span className="block text-sm">🔵 Easy</span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">Expand 3x</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Feedback on Interval Update */
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
                    <div className="text-xs text-slate-200">
                      {spacedFeedback.feedback_message}
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={handleNextFlashcard}
                        className="btn-cyber text-xs py-2 px-5 flex items-center gap-1.5 bg-emerald-400/20 border-emerald-400 text-emerald-200"
                      >
                        Next Flashcard <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW C3: STANDARD PRACTICE EXERCISE (For Workflows A, B, C-Practice)
         ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'workflows' && activeWorkflow && activeQuestion && activeWorkflow.workflow_type !== 'revise_previous_topics' && !mockExamSession && (
        <div className="space-y-6">

          {/* Workflow A Progress Header */}
          {activeWorkflow.workflow_type === 'continue_learning' && (
            <div className="glass-card p-6 border-cyan-400/30 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <Layers size={18} className="text-cyan-400" />
                  <span className="font-display font-bold text-white text-base">Curriculum Progression Checkpoint</span>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold">
                  {activeWorkflow.mastered_count} / {activeWorkflow.total_curriculum_topics} KCs Mastered ({activeWorkflow.curriculum_progress_pct}%)
                </span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/10">
                <div
                  className="bg-cyan-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${activeWorkflow.curriculum_progress_pct}%` }}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-0.5">
                  <span className="text-slate-400 text-[11px] block">Last Completed Concept:</span>
                  <span className="text-white font-medium capitalize">
                    {activeWorkflow.last_completed_concept ? activeWorkflow.last_completed_concept.replace(/_/g, ' ') : 'Curriculum Start'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-cyan-400/10 border border-cyan-400/30 space-y-0.5">
                  <span className="text-cyan-300 text-[11px] block">Next Prerequisite-Eligible Concept:</span>
                  <span className="text-white font-bold capitalize">
                    {activeWorkflow.next_recommended_concept.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Workflow B Remediation Header */}
          {activeWorkflow.workflow_type === 'improve_weak_topics' && (
            <div className="glass-card p-6 border-red-400/30 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <Zap size={18} className="text-red-400" />
                  <span className="font-display font-bold text-white text-base">Knowledge Gap Remediation</span>
                </div>
                <span className="badge-chip text-xs text-red-300 bg-red-400/15 border border-red-400/30 capitalize">
                  {activeWorkflow.intervention_type.replace(/_/g, ' ')}
                </span>
              </div>
              {activeWorkflow.prerequisite_gap && (
                <div className="p-3.5 rounded-xl bg-yellow-400/10 border border-yellow-400/30 text-xs text-yellow-200 flex items-center gap-2">
                  <ShieldAlert size={16} className="text-yellow-400 flex-shrink-0" />
                  <span>
                    Prerequisite Gap Detected: Foundational concept <strong>'{activeWorkflow.prerequisite_gap.topic.replace(/_/g, ' ')}'</strong> is unmastered ({activeWorkflow.prerequisite_gap.mastery_pct}%). Scaffolding prerequisite before advancing.
                  </span>
                </div>
              )}
              {activeWorkflow.weak_concepts_ranked && (
                <div className="space-y-1.5 pt-1">
                  <span className="text-slate-400 text-[11px] block">Lowest-Mastery Concepts Ranked:</span>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    {activeWorkflow.weak_concepts_ranked.map(w => (
                      <div key={w.topic} className={`p-2.5 rounded-lg border text-center ${w.topic === activeWorkflow.selected_concept ? 'bg-red-400/15 border-red-400 text-white font-bold' : 'bg-white/4 border-white/8 text-slate-300'}`}>
                        <div className="text-[10px] capitalize truncate">{w.topic.replace(/_/g, ' ')}</div>
                        <div className="font-mono text-xs text-red-300 mt-0.5">{w.mastery_pct}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Workflow C Study Plan Header */}
          {activeWorkflow.workflow_type === 'prepare_for_exam' && activeWorkflow.exam_plan && (
            <div className="glass-card p-6 border-purple-400/30 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <Calendar size={18} className="text-purple-400" />
                  <span className="font-display font-bold text-white text-base">{activeWorkflow.exam_plan.exam_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="badge-chip text-xs text-purple-300 bg-purple-400/15 border border-purple-400/30">
                    {activeWorkflow.days_remaining} Days Remaining
                  </span>
                  <button
                    onClick={handleStartMockExam}
                    className="btn-cyber text-xs py-1 px-3 bg-purple-500/20 border-purple-400 text-purple-200 flex items-center gap-1.5"
                  >
                    <Timer size={12} />
                    Take Timed Mock Exam
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Pedagogical Rationale */}
          {activeWorkflow.reason && (
            <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5">
              <Sparkles size={16} className="text-cyan-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-white block mb-0.5">Pedagogical Decision Rationale:</strong>
                <span>{activeWorkflow.reason}</span>
                <span className="block mt-1 text-[11px] font-mono text-slate-500">
                  Policy Source: {activeWorkflow.recommendation_source}
                </span>
              </div>
            </div>
          )}

          {/* Active Question Box */}
          <div className="glass-card p-6 space-y-5">
            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-white/10 pb-4">
              <div className="flex items-center gap-2">
                <span className="badge-chip text-xs text-cyan-300 bg-cyan-400/15 border border-cyan-400/30 capitalize">
                  {activeQuestion.topic?.replace(/_/g, ' ')}
                </span>
                <span className="badge-chip text-[10px] text-slate-400 bg-white/5 border border-white/10">
                  Difficulty {activeQuestion.difficulty}/5
                </span>
                <span className="text-xs font-mono text-slate-500">{activeQuestion.item_id}</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <span>Score: <strong className="text-green-400">{sessionSummary.questions_correct}</strong> / {sessionSummary.questions_answered}</span>
              </div>
            </div>

            {/* Prompt */}
            <div className="text-base text-white font-medium leading-relaxed">
              {activeQuestion.question}
            </div>

            {/* Options */}
            <div className="space-y-2.5 pt-1">
              {(activeQuestion.options || []).map((opt, idx) => {
                const isSelected = selectedOption === opt;
                const isSubmitted = !!stepFeedback;
                const isCorrect = isSubmitted && opt.trim().toLowerCase() === stepFeedback.correct_answer.trim().toLowerCase();
                const isWrongSelected = isSubmitted && isSelected && !isCorrect;

                let optClass = 'glass-card border-white/10 hover:border-cyan-400/40 text-slate-200';
                if (isSelected && !isSubmitted) optClass = 'border-cyan-400 bg-cyan-400/10 text-white';
                else if (isCorrect) optClass = 'border-green-400 bg-green-400/10 text-green-200 font-semibold';
                else if (isWrongSelected) optClass = 'border-red-400 bg-red-400/10 text-red-200';

                return (
                  <button
                    key={idx}
                    onClick={() => !stepFeedback && setSelectedOption(opt)}
                    disabled={submittingStep || isSubmitted}
                    className={`w-full p-4 rounded-xl border text-left text-xs transition flex items-center justify-between gap-3 ${optClass}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-[11px] font-bold ${isSelected ? 'bg-cyan-400 text-black' : 'bg-white/5 text-slate-400'}`}>
                        {String.fromCharCode(65 + idx)}
                      </span>
                      <span className="leading-relaxed">{opt}</span>
                    </div>
                    {isCorrect && <CheckCircle2 size={16} className="text-green-400 flex-shrink-0" />}
                    {isWrongSelected && <XCircle size={16} className="text-red-400 flex-shrink-0" />}
                  </button>
                );
              })}
            </div>

            {/* Submit & Assistance Toolbar */}
            <div className="pt-2 flex items-center justify-between flex-wrap gap-3">
              {/* 4 Working Assistance Buttons */}
              <div className="flex items-center flex-wrap gap-2">
                <button
                  onClick={() => requestAssistance('explain')}
                  disabled={assistanceLoading || submittingStep}
                  className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1.5 text-slate-300 hover:text-white"
                  title="Comprehensive 9-point concept explanation adapted to your level"
                >
                  <BookOpen size={13} className="text-cyan-400" />
                  Explain Concept
                </button>
                <button
                  onClick={() => requestAssistance('worked_example')}
                  disabled={assistanceLoading || submittingStep}
                  className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1.5 text-slate-300 hover:text-white"
                  title="Full 10-point step-by-step worked example with code"
                >
                  <Sparkles size={13} className="text-purple-400" />
                  Show Worked Example
                </button>
                <button
                  onClick={() => requestAssistance('easier_step')}
                  disabled={assistanceLoading || submittingStep}
                  className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1.5 text-yellow-300 border-yellow-400/40 hover:border-yellow-400"
                  title="Calibrated Level 1-2 foundational question"
                >
                  <ShieldAlert size={13} />
                  Need an Easier Step
                </button>
                <button
                  onClick={() => requestAssistance('inspect_prerequisites')}
                  disabled={assistanceLoading || submittingStep}
                  className="btn-cyber text-xs py-1.5 px-3 flex items-center gap-1.5 text-slate-300 hover:text-white"
                  title="Inspect DAG dependency status and gaps"
                >
                  <Layers size={13} className="text-emerald-400" />
                  Inspect Prerequisites
                </button>
              </div>

              {!stepFeedback ? (
                <button
                  onClick={handleAnswerSubmit}
                  disabled={!selectedOption || submittingStep}
                  className="btn-cyber-solid text-xs py-2 px-5 flex items-center gap-2"
                >
                  {submittingStep ? <RefreshCw size={14} className="animate-spin" /> : null}
                  Submit Response <ArrowRight size={14} />
                </button>
              ) : (
                <button
                  onClick={handleAdvanceToNext}
                  className="btn-cyber text-xs py-2 px-5 flex items-center gap-2 bg-cyan-400/20 border-cyan-400 text-cyan-200"
                >
                  Next Question <ChevronRight size={14} />
                </button>
              )}
            </div>

            {/* Step Feedback & Difficulty Adaptation Banner */}
            {stepFeedback && (
              <div className={`p-4 rounded-xl border text-xs leading-relaxed space-y-2 mt-4 ${stepFeedback.is_correct ? 'bg-green-400/10 border-green-400/30 text-green-200' : 'bg-red-400/10 border-red-400/30 text-red-200'}`}>
                <div className="flex items-center justify-between">
                  <div className="font-semibold flex items-center gap-2">
                    {stepFeedback.is_correct ? <CheckCircle2 size={16} className="text-green-400" /> : <XCircle size={16} className="text-red-400" />}
                    <span>{stepFeedback.is_correct ? 'Correct Answer!' : 'Incorrect Attempt'}</span>
                  </div>
                  <span className="font-mono text-[11px] text-white">
                    Updated Mastery: {stepFeedback.updated_mastery_pct}%
                  </span>
                </div>
                <p className="text-slate-200">{stepFeedback.explanation}</p>
                {stepFeedback.distractor_insight && (
                  <div className="p-2.5 rounded-lg bg-black/40 text-amber-200 border border-amber-400/20 text-[11px]">
                    <strong>Distractor Analysis:</strong> {stepFeedback.distractor_insight}
                  </div>
                )}
                <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-300">
                  <span>
                    Dynamic Difficulty Adaptation: <strong>{stepFeedback.difficulty_adaptation === 'harder' ? 'Advancing to More Challenging Exercise' : stepFeedback.difficulty_adaptation === 'easier' ? 'Stepping Down to Foundational Exercise' : 'Maintaining Calibrated Challenge Level'}</strong>
                  </span>
                  <span className="badge-chip text-[10px] text-cyan-300 bg-cyan-400/15 border border-cyan-400/30">
                    Level {stepFeedback.new_difficulty}/5
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          MODAL: ASSISTANCE FEATURES (Explain, Worked Example, Prerequisites)
         ════════════════════════════════════════════════════════════════════ */}
      {assistanceType && assistanceData && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-2xl w-full p-6 space-y-4 border-cyan-400/40 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => { setAssistanceType(null); setAssistanceData(null); }}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X size={18} />
            </button>

            {/* 1. Explain Concept Modal */}
            {assistanceType === 'explain' && (
              <div className="space-y-4 text-xs">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3">
                  <BookOpen size={18} className="text-cyan-400" />
                  <h3 className="font-display font-bold text-base text-white">{assistanceData.title}</h3>
                </div>

                {/* Learner Level Adaptation Badge */}
                {assistanceData.content?.learner_level_adaptation && (
                  <div className="p-3 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-between">
                    <span className="text-cyan-300 font-medium">Adapted for: {assistanceData.content.learner_level_adaptation.tier}</span>
                    <span className="font-mono text-white font-bold">{assistanceData.content.learner_level_adaptation.current_mastery_pct}% Mastery</span>
                  </div>
                )}

                <div className="space-y-3">
                  <div>
                    <h5 className="font-semibold text-white mb-1">Concept Definition:</h5>
                    <p className="text-slate-300 leading-relaxed">{assistanceData.content?.definition}</p>
                  </div>
                  <div>
                    <h5 className="font-semibold text-white mb-1">Why It Matters:</h5>
                    <p className="text-slate-300 leading-relaxed">{assistanceData.content?.why_it_matters}</p>
                  </div>
                  {assistanceData.content?.formula_or_syntax && (
                    <div>
                      <h5 className="font-semibold text-white mb-1">Key Formula / Computational Representation:</h5>
                      <pre className="p-2.5 rounded-lg bg-black/40 text-cyan-300 font-mono text-[11px] overflow-x-auto">
                        {assistanceData.content.formula_or_syntax}
                      </pre>
                    </div>
                  )}
                  {assistanceData.content?.step_by_step_reasoning && (
                    <div>
                      <h5 className="font-semibold text-white mb-1">Logical Reasoning Workflow:</h5>
                      <ul className="list-disc list-inside space-y-1 text-slate-300 pl-1">
                        {assistanceData.content.step_by_step_reasoning.map((step, sIdx) => (
                          <li key={sIdx}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {assistanceData.content?.common_misconceptions && (
                    <div className="p-3 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-200">
                      <strong>Common Pitfall:</strong> {assistanceData.content.common_misconceptions}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 2. Show Worked Example Modal */}
            {assistanceType === 'worked_example' && assistanceData.worked_example && (
              <div className="space-y-4 text-xs">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3">
                  <Sparkles size={18} className="text-purple-400" />
                  <h3 className="font-display font-bold text-base text-white">{assistanceData.title}</h3>
                </div>
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-slate-200 font-medium">
                  {assistanceData.worked_example.problem_statement}
                </div>
                <div className="space-y-3">
                  {(assistanceData.worked_example.steps || []).map((step, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/4 border border-white/8 space-y-1.5">
                      <div className="font-semibold text-cyan-400 flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-cyan-400/20 text-cyan-300 flex items-center justify-center text-[10px]">
                          {step.step_number || idx + 1}
                        </span>
                        <span>{step.title}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{step.explanation}</p>
                      {step.math && (
                        <pre className="p-2 rounded-lg bg-black/40 text-slate-200 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap">
                          {step.math}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
                {assistanceData.worked_example.key_takeaway && (
                  <div className="p-3 rounded-xl bg-purple-400/10 border border-purple-400/30 text-purple-200">
                    <strong>Key Engineering Takeaway:</strong> {assistanceData.worked_example.key_takeaway}
                  </div>
                )}
              </div>
            )}

            {/* 3. Inspect Prerequisites Modal */}
            {assistanceType === 'inspect_prerequisites' && (
              <div className="space-y-4 text-xs">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3">
                  <Layers size={18} className="text-emerald-400" />
                  <h3 className="font-display font-bold text-base text-white">
                    Prerequisite Dependency Inspection: {assistanceData.target_topic?.replace(/_/g, ' ').toUpperCase()}
                  </h3>
                </div>
                <p className="text-slate-300">{assistanceData.recommendation}</p>
                <div className="space-y-2">
                  <h5 className="font-semibold text-white">Required Foundation Components:</h5>
                  {(assistanceData.prerequisites || []).map(p => (
                    <div key={p.topic} className={`p-3 rounded-xl border flex items-center justify-between gap-3 ${
                      p.badge_color === 'green' ? 'bg-green-400/10 border-green-400/30' : p.badge_color === 'red' ? 'bg-red-400/10 border-red-400/30' : 'bg-yellow-400/10 border-yellow-400/30'
                    }`}>
                      <div>
                        <div className="font-bold text-white capitalize">{p.title}</div>
                        <div className="text-[11px] text-slate-400">{p.description}</div>
                      </div>
                      <div className="text-right">
                        <span className={`badge-chip text-[10px] ${
                          p.badge_color === 'green' ? 'text-green-300 bg-green-400/20' : p.badge_color === 'red' ? 'text-red-300 bg-red-400/20' : 'text-yellow-300 bg-yellow-400/20'
                        }`}>
                          {p.status}
                        </span>
                        <div className="font-mono text-white text-[11px] mt-0.5">{p.mastery_pct}%</div>
                      </div>
                    </div>
                  ))}
                  {(!assistanceData.prerequisites || assistanceData.prerequisites.length === 0) && (
                    <div className="text-center py-4 text-slate-400">
                      This is a foundational Layer-0 concept with no upstream prerequisites.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          MODAL: EXAM PREPARATION SETUP
         ════════════════════════════════════════════════════════════════════ */}
      {showExamSetup && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-xl w-full p-6 space-y-5 border-purple-400/40 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowExamSetup(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X size={18} />
            </button>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Calendar size={18} className="text-purple-400" />
                <h3 className="font-display font-bold text-lg text-white">Configure Personalized Exam Roadmap</h3>
              </div>
              <p className="text-slate-400 text-xs">
                Creates a day-by-day study schedule with topological ordering, timed mock exams, and dynamic rebalancing.
              </p>
            </div>

            <form onSubmit={handleConfigureExamPlan} className="space-y-4 text-xs">
              <div>
                <label className="text-slate-300 block mb-1 font-medium">Target Exam Date:</label>
                <input
                  type="date"
                  value={examForm.date}
                  onChange={e => setExamForm({ ...examForm, date: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-purple-400 outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 block mb-1 font-medium">Daily Study Time (mins):</label>
                  <input
                    type="number"
                    min={15}
                    max={240}
                    value={examForm.minutes}
                    onChange={e => setExamForm({ ...examForm, minutes: Number(e.target.value) })}
                    className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-purple-400 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-300 block mb-1 font-medium">Target Exam Score (%):</label>
                  <input
                    type="number"
                    min={50}
                    max={100}
                    value={examForm.targetScore}
                    onChange={e => setExamForm({ ...examForm, targetScore: Number(e.target.value) })}
                    className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-purple-400 outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-300 block mb-1.5 font-medium">
                  Syllabus Topics ({examForm.selectedTopics.length} Selected):
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-2 rounded-xl bg-black/40 border border-white/10">
                  {ALL_TOPICS.map(t => {
                    const sel = examForm.selectedTopics.includes(t);
                    return (
                      <button
                        type="button"
                        key={t}
                        onClick={() => toggleTopic(t)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] capitalize transition ${sel ? 'bg-purple-500/30 text-purple-200 border border-purple-400/50' : 'bg-white/5 text-slate-400 hover:text-white border border-transparent'}`}
                      >
                        {t.replace(/_/g, ' ')}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowExamSetup(false)}
                  className="btn-cyber text-xs py-2 px-4"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={workflowLoading || examForm.selectedTopics.length === 0}
                  className="btn-cyber-solid text-xs py-2 px-5 bg-purple-500 hover:bg-purple-400 border-purple-400"
                >
                  {workflowLoading ? 'Generating Roadmap...' : 'Generate Exam Roadmap'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
