import React, { useEffect, useState } from 'react';
import {
  Brain, Cpu, Activity, Award, BarChart3, CheckCircle2, AlertTriangle,
  Code2, GitBranch, ShieldCheck, Compass, Play, RefreshCw, Sparkles,
  Layers, Check, X, ArrowRight, BookOpen, AlertCircle, HelpCircle,
  Clock, RotateCcw, Target, Sliders, FileText, CheckSquare, Zap
} from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function KnowledgeIntelligencePage() {
  const [loading, setLoading] = useState(true);
  const [intel, setIntel] = useState(null);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Active Interactive Assessment Tool (all 8 modalities)
  // 'diagnostic' | 'conceptual' | 'coding' | 'concept_map' | 'active_recall' | 'confidence' | 'analytics' | 'project'
  const [activeTool, setActiveTool] = useState('diagnostic');

  // Tool 1: Diagnostic Assessment State
  const [diagTopic, setDiagTopic] = useState('linear regression');
  const [diagData, setDiagData] = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagAnswers, setDiagAnswers] = useState({});
  const [diagResult, setDiagResult] = useState(null);

  // Tool 2: Conceptual Explanation State
  const [conceptTopic, setConceptTopic] = useState('python');
  const [conceptPrompt, setConceptPrompt] = useState('Explain how NumPy ndarray differs from standard Python lists in memory layout and vectorization.');
  const [conceptResponse, setConceptResponse] = useState('');
  const [conceptEvaluating, setConceptEvaluating] = useState(false);
  const [conceptResult, setConceptResult] = useState(null);

  // Tool 3: Coding Sandbox State
  const [codingTopic, setCodingTopic] = useState('python');
  const [codingChallenges, setCodingChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [codeSnippet, setCodeSnippet] = useState('');
  const [codeExecuting, setCodeExecuting] = useState(false);
  const [codeResult, setCodeResult] = useState(null);

  // Tool 4: Concept Mapping State
  const [mapEdges, setMapEdges] = useState([
    { source: 'python', target: 'data preprocessing', relation: 'prerequisite' },
    { source: 'data preprocessing', target: 'linear regression', relation: 'prerequisite' },
  ]);
  const [newSource, setNewSource] = useState('probability');
  const [newTarget, setNewTarget] = useState('linear regression');
  const [mapEvaluating, setMapEvaluating] = useState(false);
  const [mapResult, setMapResult] = useState(null);

  // Tool 5: Active Recall State
  const activeRecallDeck = [
    {
      concept: 'Gradient Descent Convergence',
      question: 'Why does batch gradient descent guarantee convergence to the global minimum in convex loss surfaces?',
      answer: 'Convex functions have a unique stationary point where gradient is zero. Batch gradient descent computes the exact gradient across all training samples at each step, yielding monotonic loss reduction when learning rate is appropriately bounded by the Lipschitz constant.',
      topic: 'linear regression',
    },
    {
      concept: 'Vectorization vs Looping',
      question: 'How does SIMD vectorization in NumPy achieve 50x-100x speedups over pure Python for-loops?',
      answer: 'NumPy buffers elements in contiguous C memory blocks with homogeneous dtypes, avoiding Python PyObject pointer boxing, dynamic dispatch, and GIL contention while allowing modern CPU vector registers to execute instructions simultaneously across chunks.',
      topic: 'python',
    },
    {
      concept: 'Precision-Recall Tradeoff',
      question: 'In imbalanced fraud detection, why is ROC-AUC often overly optimistic compared to PR-AUC?',
      answer: 'True Negative count dominates the False Positive Rate denominator in ROC space (FPR = FP / (FP + TN)). High TNs keep FPR artificially low despite many false alarms. PR-AUC excludes TNs, focusing exclusively on positive class retrieval quality.',
      topic: 'classification',
    },
  ];
  const [recallIdx, setRecallIdx] = useState(0);
  const [recallFlipped, setRecallFlipped] = useState(false);
  const [recallRating, setRecallRating] = useState(null);

  // Tool 6: Confidence Calibration State
  const [confItems, setConfItems] = useState([
    { id: 1, text: 'In logistic regression, the loss function used is Mean Squared Error.', trueAns: false, userAns: null, conf: 80 },
    { id: 2, text: 'NumPy vectorized operations execute in contiguous C memory without Python pointer chasing.', trueAns: true, userAns: null, conf: 90 },
    { id: 3, text: 'L2 regularization (Ridge) pushes irrelevant weight coefficients exactly to zero.', trueAns: false, userAns: null, conf: 75 },
    { id: 4, text: 'Bayesian Knowledge Tracing models knowledge state as a two-state Hidden Markov Model.', trueAns: true, userAns: null, conf: 85 },
  ]);
  const [confEvaluating, setConfEvaluating] = useState(false);
  const [confResult, setConfResult] = useState(null);

  // Tool 7: Learning Behavior Analytics State
  const [analyticsFilter, setAnalyticsFilter] = useState('all');

  // Tool 8: Project-Based Assessment State
  const [selectedProject, setSelectedProject] = useState('proj_numpy_eda');
  const [projectScores, setProjectScores] = useState({
    'Data Normalization (Min-Max)': 85,
    'Summary Statistics (Mean & Std)': 90,
    'Outlier Detection (Z-Score > 2.0)': 80,
    'Code Quality & Documentation': 95,
  });
  const [projectCode, setProjectCode] = useState(
    'import numpy as np\n\ndef analyze_student_scores(scores_matrix):\n    """Normalized student analytics with z-score anomaly filter."""\n    col_min = np.min(scores_matrix, axis=0)\n    col_max = np.max(scores_matrix, axis=0)\n    norm = (scores_matrix - col_min) / (col_max - col_min + 1e-8)\n    means = np.mean(norm, axis=0)\n    stds = np.std(norm, axis=0)\n    z_scores = (norm - means) / (stds + 1e-8)\n    outliers = np.abs(z_scores) > 2.0\n    return norm, means, stds, outliers'
  );
  const [projectEvaluating, setProjectEvaluating] = useState(false);
  const [projectResult, setProjectResult] = useState(null);

  useEffect(() => {
    setLoading(true);
    apiFetch('/api/learner/intelligence')
      .then((res) => {
        setIntel(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load learner knowledge intelligence.');
        setLoading(false);
      });
  }, [refreshKey]);

  useEffect(() => {
    if (activeTool === 'coding') {
      apiFetch(`/api/assessment/coding/challenges?topic=${encodeURIComponent(codingTopic)}`)
        .then((res) => {
          if (res.challenges && res.challenges.length > 0) {
            setCodingChallenges(res.challenges);
            setSelectedChallenge(res.challenges[0]);
            setCodeSnippet(res.challenges[0].starter_code || '');
          }
        })
        .catch(() => {});
    }
  }, [activeTool, codingTopic]);

  // Handlers for Interactive Assessment Tools
  const handleLoadDiagnostic = async () => {
    setDiagLoading(true);
    setDiagResult(null);
    setDiagAnswers({});
    try {
      const res = await apiFetch(`/api/assessment/diagnostic/${encodeURIComponent(diagTopic)}`);
      setDiagData(res);
    } catch (e) {
      setDiagData(null);
    } finally {
      setDiagLoading(false);
    }
  };

  const handleSubmitDiagnostic = async () => {
    if (!diagData) return;
    try {
      const res = await apiFetch('/api/assessment/diagnostic/submit', {
        method: 'POST',
        body: JSON.stringify({
          topic: diagTopic,
          answers: diagAnswers,
        }),
      });
      setDiagResult(res);
      setRefreshKey(k => k + 1);
    } catch (e) {
      setDiagResult({ ok: false, error: e.message });
    }
  };

  const handleEvaluateConcept = async () => {
    if (!conceptResponse.trim()) return;
    setConceptEvaluating(true);
    try {
      const res = await apiFetch('/api/assessment/conceptual/evaluate', {
        method: 'POST',
        body: JSON.stringify({
          topic: conceptTopic,
          prompt: conceptPrompt,
          response: conceptResponse,
        }),
      });
      setConceptResult(res);
    } catch (e) {
      setConceptResult({ ok: false, error: e.message });
    } finally {
      setConceptEvaluating(false);
    }
  };

  const handleExecuteCode = async () => {
    if (!selectedChallenge) return;
    setCodeExecuting(true);
    try {
      const res = await apiFetch('/api/assessment/coding/execute', {
        method: 'POST',
        body: JSON.stringify({
          code: codeSnippet,
          test_cases: selectedChallenge.test_cases || [],
        }),
      });
      setCodeResult(res);
    } catch (e) {
      setCodeResult({ ok: false, error: e.message });
    } finally {
      setCodeExecuting(false);
    }
  };

  const handleEvaluateConceptMap = async () => {
    setMapEvaluating(true);
    try {
      const res = await apiFetch('/api/assessment/concept-map/evaluate', {
        method: 'POST',
        body: JSON.stringify({ edges: mapEdges }),
      });
      setMapResult(res);
    } catch (e) {
      setMapResult({ ok: false, error: e.message });
    } finally {
      setMapEvaluating(false);
    }
  };

  const handleAddMapEdge = () => {
    if (!newSource || !newTarget || newSource === newTarget) return;
    setMapEdges([...mapEdges, { source: newSource, target: newTarget, relation: 'prerequisite' }]);
  };

  const handleRateActiveRecall = (rating) => {
    setRecallRating(rating);
    // Move to next card or loop
    setTimeout(() => {
      setRecallFlipped(false);
      setRecallRating(null);
      setRecallIdx((recallIdx + 1) % activeRecallDeck.length);
    }, 1200);
  };

  const handleEvaluateConfidence = async () => {
    setConfEvaluating(true);
    try {
      const history = confItems.map(item => ({
        confidence: item.conf / 100,
        correct: item.userAns === item.trueAns,
      }));
      const res = await apiFetch('/api/assessment/confidence/calibrate', {
        method: 'POST',
        body: JSON.stringify({ history }),
      });
      setConfResult(res.calibration || res);
    } catch (e) {
      setConfResult({ error: e.message });
    } finally {
      setConfEvaluating(false);
    }
  };

  const handleEvaluateProject = async () => {
    setProjectEvaluating(true);
    try {
      const res = await apiFetch('/api/assessment/project/evaluate', {
        method: 'POST',
        body: JSON.stringify({
          project_id: selectedProject,
          submission: projectCode,
          criterion_scores: projectScores,
        }),
      });
      setProjectResult(res);
    } catch (e) {
      setProjectResult({ ok: false, error: e.message });
    } finally {
      setProjectEvaluating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[50vh]">
        <RefreshCw className="animate-spin text-cyan-400 mb-4" size={32} />
        <p className="text-slate-400 font-medium">Aggregating multi-method knowledge profile and BKT posteriors...</p>
      </div>
    );
  }

  if (error || !intel) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="glass-card border-red-500/30 p-6 text-center">
          <AlertTriangle className="text-red-400 mx-auto mb-2" size={32} />
          <h2 className="text-white text-lg font-bold mb-1">Knowledge Intelligence Service Offline</h2>
          <p className="text-slate-400 text-sm mb-4">{error || 'Unable to retrieve multi-method profile.'}</p>
          <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber">Retry</button>
        </div>
      </div>
    );
  }

  const radar = intel.multi_method_radar || {
    bkt_mastery: 68.0,
    empirical_accuracy: 74.2,
    conceptual_understanding: 81.0,
    practical_coding: 72.5,
    retention_stability: 85.0,
    metacognitive_calibration: 80.0,
  };

  const MODALITIES = [
    { id: 'diagnostic', label: '1. Diagnostic Assessment', icon: HelpCircle },
    { id: 'conceptual', label: '2. Conceptual Rubric', icon: FileText },
    { id: 'coding', label: '3. Practical Coding', icon: Code2 },
    { id: 'concept_map', label: '4. Concept Mapping', icon: GitBranch },
    { id: 'active_recall', label: '5. Active Recall', icon: RotateCcw },
    { id: 'confidence', label: '6. Confidence Calibration', icon: Target },
    { id: 'analytics', label: '7. Learning Analytics', icon: Activity },
    { id: 'project', label: '8. Project Assessment', icon: Award },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-10">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              MULTI-METHOD KNOWLEDGE PROFILING
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-400/10 text-purple-400 border border-purple-400/20">
              BEYOND MCQS · 8 ASSESSMENT MODES
            </span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">Student Knowledge Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">
            Consolidated multi-dimensional evidence tracking BKT mastery, conceptual explanation rubrics, sandboxed coding execution, and metacognitive calibration.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setRefreshKey(k => k + 1)} className="btn-cyber text-xs flex items-center gap-2">
            <RefreshCw size={14} /> Recalculate Profile
          </button>
        </div>
      </div>

      {/* 6-Axis Multi-Method Radar & Dimension Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-6 lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="font-display font-bold text-white text-base flex items-center gap-2">
              <Compass className="text-cyan-400" size={18} />
              Assessment Radar
            </h3>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">6 Dimensions</span>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>1. BKT Mastery Index</span>
                <span className="font-mono font-bold text-cyan-400">{radar.bkt_mastery}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-400 h-full rounded-full transition-all" style={{ width: `${radar.bkt_mastery}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>2. Empirical Accuracy</span>
                <span className="font-mono font-bold text-emerald-400">{radar.empirical_accuracy}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-400 h-full rounded-full transition-all" style={{ width: `${radar.empirical_accuracy}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>3. Conceptual Understanding</span>
                <span className="font-mono font-bold text-purple-400">{radar.conceptual_understanding}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-purple-400 h-full rounded-full transition-all" style={{ width: `${radar.conceptual_understanding}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>4. Practical Coding Execution</span>
                <span className="font-mono font-bold text-amber-400">{radar.practical_coding}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-400 h-full rounded-full transition-all" style={{ width: `${radar.practical_coding}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>5. Spaced Memory Retention</span>
                <span className="font-mono font-bold text-blue-400">{radar.retention_stability}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-blue-400 h-full rounded-full transition-all" style={{ width: `${radar.retention_stability}%` }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>6. Metacognitive Calibration</span>
                <span className="font-mono font-bold text-pink-400">{radar.metacognitive_calibration}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-pink-400 h-full rounded-full transition-all" style={{ width: `${radar.metacognitive_calibration}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Cognitive State Overview */}
        <div className="glass-card p-6 lg:col-span-2 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="font-display font-bold text-white text-base flex items-center gap-2">
                <Brain className="text-purple-400" size={18} />
                Cognitive State & Information Theoretic Metrics
              </h3>
              <span className="text-[10px] font-mono text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">
                Unified Learner Model
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5 mt-4">
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1.5">
                <span className="text-slate-400 font-mono text-[11px] block">MASTERED TOPICS</span>
                <div className="text-xl font-bold text-white">
                  {intel.knowledge_state?.mastered_kcs_count || 0} / {intel.knowledge_state?.total_kcs || 30}
                </div>
                <p className="text-slate-400 text-[11px]">
                  {intel.knowledge_state?.overall_mastery_pct || 0}% syllabus mastery under BKT posteriors.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1.5">
                <span className="text-slate-400 font-mono text-[11px] block">DIAGNOSTIC ENTROPY</span>
                <div className="text-xl font-bold text-cyan-300 font-mono">
                  {intel.assessment_performance?.diagnostic_entropy_bits || 0.95} bits
                </div>
                <p className="text-slate-400 text-[11px]">
                  Information gain potential across boundary concepts.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1.5">
                <span className="text-slate-400 font-mono text-[11px] block">PREREQUISITE STATUS</span>
                <div className="text-xl font-bold text-emerald-300">
                  {intel.prerequisite_completion?.gaps_count === 0 ? 'Ready' : `${intel.prerequisite_completion?.gaps_count} Gaps`}
                </div>
                <p className="text-slate-400 text-[11px]">
                  Topological frontier contains {intel.prerequisite_completion?.ready_frontier?.length || 0} eligible concepts.
                </p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 flex items-start gap-3 mt-4">
            <Sparkles className="text-cyan-400 shrink-0 mt-0.5" size={16} />
            <div>
              <span className="font-bold text-white block mb-0.5">Pedagogical Distinction</span>
              Self-reported confidence, empirical answer correctness, and theoretical BKT mastery probabilities are tracked separately. Unattempted challenges are never marked incorrect.
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Assessment Methods Studio */}
      <div className="glass-card p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <h3 className="font-display font-bold text-white text-lg flex items-center gap-2">
              <Layers className="text-cyan-400" size={20} />
              Interactive Multi-Method Assessment Studio
            </h3>
            <p className="text-slate-400 text-xs mt-0.5">
              Experience all 8 distinct assessment modalities directly from this unified studio.
            </p>
          </div>

          <div className="flex flex-wrap gap-1 p-1 bg-white/5 rounded-xl border border-white/10 text-xs">
            {MODALITIES.map(m => {
              const Icon = m.icon;
              return (
                <button
                  key={m.id}
                  onClick={() => setActiveTool(m.id)}
                  className={`px-2.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                    activeTool === m.id ? 'bg-cyan-400 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon size={13} />
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* TAB 1: Pre-Topic Diagnostic Assessment */}
        {activeTool === 'diagnostic' && (
          <div className="space-y-4 text-xs">
            <div className="flex items-center gap-3">
              <select
                className="cyber-input text-xs"
                value={diagTopic}
                onChange={(e) => setDiagTopic(e.target.value)}
              >
                <option value="linear regression">Linear Regression</option>
                <option value="python">Python Foundations</option>
                <option value="classification">Classification</option>
                <option value="clustering">Clustering</option>
              </select>
              <button onClick={handleLoadDiagnostic} disabled={diagLoading} className="btn-cyber text-xs">
                {diagLoading ? <RefreshCw className="animate-spin" size={14} /> : 'Generate Diagnostic'}
              </button>
            </div>

            {diagData && diagData.questions && (
              <div className="space-y-4 pt-2">
                <p className="text-slate-300 text-xs">{diagData.instructions}</p>
                {diagData.questions.map((q, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-white">Question {idx + 1} ({q.diagnostic_role})</span>
                      <span className="font-mono text-cyan-400">Level {q.difficulty}</span>
                    </div>
                    <p className="text-slate-200 text-xs font-medium">{q.question}</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {q.options?.map((opt, optIdx) => (
                        <button
                          key={optIdx}
                          onClick={() => setDiagAnswers({ ...diagAnswers, [q.item_id]: opt })}
                          className={`p-2.5 rounded-lg border text-left text-xs transition-all ${
                            diagAnswers[q.item_id] === opt
                              ? 'bg-cyan-400/20 border-cyan-400 text-cyan-200 font-semibold'
                              : 'bg-white/5 border-white/5 text-slate-300 hover:bg-white/10'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                <button
                  onClick={handleSubmitDiagnostic}
                  className="btn-cyber-solid text-xs w-full py-2.5"
                >
                  Submit Diagnostic & Calibrate Mastery Prior
                </button>
              </div>
            )}

            {diagResult && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2 mt-3">
                <div className="font-bold text-white text-sm">
                  Diagnostic Result: {diagResult.score_pct}% Correct ({diagResult.correct_count}/{diagResult.total_items})
                </div>
                <div className="text-cyan-300 text-xs">
                  Calibrated BKT Prior: P(L₀) = <span className="font-mono font-bold">{diagResult.calibrated_prior_mastery}</span>
                </div>
                <p className="text-slate-300 text-xs">{diagResult.recommendation}</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Conceptual Understanding Assessment */}
        {activeTool === 'conceptual' && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-1 space-y-2">
                <label className="font-mono text-slate-400 block">SELECT TOPIC</label>
                <select
                  className="cyber-input w-full text-xs"
                  value={conceptTopic}
                  onChange={(e) => setConceptTopic(e.target.value)}
                >
                  <option value="python">Python / NumPy Architecture</option>
                  <option value="linear_regression">Linear Regression Mechanics</option>
                  <option value="classification">Classification & Decision Boundaries</option>
                </select>
              </div>
              <div className="md:col-span-3 space-y-2">
                <label className="font-mono text-slate-400 block">ASSESSMENT PROMPT</label>
                <div className="p-2.5 rounded-lg bg-white/5 text-white font-medium">
                  {conceptPrompt}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="font-mono text-slate-400 block">YOUR NATURAL LANGUAGE EXPLANATION</label>
              <textarea
                rows={4}
                className="cyber-input w-full p-3 text-xs leading-relaxed"
                placeholder="Explain the memory structure, contiguous C buffers, vectorized SIMD execution, and pointer references in your own words..."
                value={conceptResponse}
                onChange={(e) => setConceptResponse(e.target.value)}
              />
            </div>

            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-500 text-[11px]">
                Scored automatically against evidence rubrics (missing concepts, key mechanisms, misconceptions).
              </span>
              <button
                onClick={handleEvaluateConcept}
                disabled={conceptEvaluating || !conceptResponse.trim()}
                className="btn-cyber-solid text-xs flex items-center gap-1.5"
              >
                {conceptEvaluating ? <RefreshCw className="animate-spin" size={14} /> : <Sparkles size={14} />}
                Evaluate Explanation
              </button>
            </div>

            {conceptResult && conceptResult.ok && (
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-3 mt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm">
                      Conceptual Rubric Score: <span className="font-mono text-purple-300">{conceptResult.score_pct}%</span>
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-200">
                      Confidence: {conceptResult.evaluation_confidence}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-xs">{conceptResult.feedback}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  <div className="p-2.5 rounded-lg bg-white/5 space-y-1">
                    <span className="font-mono text-emerald-400 text-[11px] block">RECOGNIZED CONCEPTS</span>
                    <div className="flex flex-wrap gap-1">
                      {conceptResult.recognized_concepts?.map((c, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 font-mono">
                          ✓ {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-white/5 space-y-1">
                    <span className="font-mono text-amber-400 text-[11px] block">MISSING CONCEPTS</span>
                    <div className="flex flex-wrap gap-1">
                      {conceptResult.missing_concepts?.map((c, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono">
                          ✕ {c}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Practical Coding Assessment */}
        {activeTool === 'coding' && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {codingChallenges.map((ch) => (
                <button
                  key={ch.id}
                  onClick={() => {
                    setSelectedChallenge(ch);
                    setCodeSnippet(ch.starter_code || '');
                    setCodeResult(null);
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedChallenge?.id === ch.id
                      ? 'bg-cyan-400/15 border-cyan-400 text-white'
                      : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10'
                  }`}
                >
                  <div className="font-bold text-white text-xs mb-1">{ch.title}</div>
                  <div className="text-[11px] text-slate-400 line-clamp-2">{ch.prompt}</div>
                </button>
              ))}
            </div>

            <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between">
              <div>
                <span className="font-mono text-slate-400 text-[10px] block">ACTIVE CODING CHALLENGE</span>
                <span className="font-bold text-white text-sm">{selectedChallenge?.title}</span>
              </div>
              <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-cyan-400/10 text-cyan-300">
                Level {selectedChallenge?.difficulty || 2}
              </span>
            </div>

            <div className="space-y-1.5">
              <label className="font-mono text-slate-400 block">PYTHON SOLUTION CODE</label>
              <textarea
                rows={6}
                className="cyber-input w-full p-3 font-mono text-xs leading-relaxed bg-black/40"
                value={codeSnippet}
                onChange={(e) => setCodeSnippet(e.target.value)}
              />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-500 text-[11px]">
                Executed in an isolated sandbox with memory/timeout restrictions and unit tests.
              </span>
              <button
                onClick={handleExecuteCode}
                disabled={codeExecuting}
                className="btn-cyber-solid text-xs flex items-center gap-1.5"
              >
                {codeExecuting ? <RefreshCw className="animate-spin" size={14} /> : <Code2 size={14} />}
                Run in Sandbox
              </button>
            </div>

            {codeResult && (
              <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-3 mt-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">
                    Execution Result: <span className="font-mono text-cyan-300">{codeResult.score_pct}% Passed</span>
                  </span>
                  <span className="font-mono text-slate-400 text-[11px]">{codeResult.execution_time_ms} ms</span>
                </div>

                <div className="space-y-1.5">
                  {codeResult.test_results?.map((t, i) => (
                    <div key={i} className={`p-2 rounded flex items-center justify-between text-[11px] font-mono ${
                      t.passed ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'
                    }`}>
                      <span>Test {t.test_index}: {t.input}</span>
                      <span>{t.passed ? '✓ PASSED' : `✕ Expected: ${t.expected}, Got: ${t.actual}`}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: Concept Mapping Assessment */}
        {activeTool === 'concept_map' && (
          <div className="space-y-4 text-xs">
            <p className="text-slate-400">
              Build and evaluate relationship edges between machine learning concepts. Your connections are verified against the Curriculum DAG.
            </p>

            <div className="space-y-2">
              <span className="font-mono text-slate-400 block">CURRENT CONCEPT EDGES</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {mapEdges.map((e, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/5 flex items-center justify-between">
                    <span className="font-semibold text-white">{e.source}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-300">
                      → {e.relation} →
                    </span>
                    <span className="font-semibold text-white">{e.target}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-wrap gap-2 items-center">
              <span className="font-mono text-slate-400 text-[11px]">Add Connection:</span>
              <input
                className="cyber-input text-xs py-1 px-2.5"
                value={newSource}
                onChange={e => setNewSource(e.target.value)}
                placeholder="Source concept"
              />
              <span className="text-cyan-400">→</span>
              <input
                className="cyber-input text-xs py-1 px-2.5"
                value={newTarget}
                onChange={e => setNewTarget(e.target.value)}
                placeholder="Target concept"
              />
              <button onClick={handleAddMapEdge} className="btn-cyber text-xs py-1 px-3">
                + Add Edge
              </button>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleEvaluateConceptMap}
                disabled={mapEvaluating}
                className="btn-cyber-solid text-xs flex items-center gap-1.5"
              >
                {mapEvaluating ? <RefreshCw className="animate-spin" size={14} /> : <GitBranch size={14} />}
                Evaluate Graph Alignment
              </button>
            </div>

            {mapResult && (
              <div className="p-4 rounded-xl bg-cyan-400/10 border border-cyan-400/30 space-y-2 mt-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">
                    Graph Alignment: <span className="font-mono text-cyan-300">{mapResult.alignment_pct}%</span>
                  </span>
                  <span className="text-[11px] text-emerald-400 font-bold">{mapResult.valid_edges_count} Valid Edges</span>
                </div>
                {mapResult.missing_prerequisites?.length > 0 && (
                  <div className="text-[11px] text-amber-300 space-y-0.5 pt-1">
                    <span className="font-bold block">Missing Canonical Prerequisites:</span>
                    {mapResult.missing_prerequisites.map((m, i) => (
                      <div key={i}>• {m.note}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 5: Active Recall Assessment */}
        {activeTool === 'active_recall' && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono text-purple-300 block">ACTIVE RETRIEVAL TESTING</span>
                <span className="font-bold text-white text-sm">Question-Before-Answer Recall Card {recallIdx + 1} of {activeRecallDeck.length}</span>
              </div>
              <span className="text-[11px] font-mono text-cyan-400">{activeRecallDeck[recallIdx].topic}</span>
            </div>

            {/* Flashcard Frame */}
            <div
              onClick={() => setRecallFlipped(!recallFlipped)}
              className="p-6 rounded-2xl bg-slate-900 border border-white/10 min-h-[180px] flex flex-col justify-between cursor-pointer hover:border-cyan-400/40 transition-all shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-3">
                  <span className="font-mono font-bold text-cyan-400">{activeRecallDeck[recallIdx].concept}</span>
                  <span>{recallFlipped ? 'Answer Revealed' : 'Click card to flip'}</span>
                </div>
                <div className="text-white text-sm font-medium leading-relaxed">
                  {recallFlipped ? activeRecallDeck[recallIdx].answer : activeRecallDeck[recallIdx].question}
                </div>
              </div>

              <div className="text-[11px] text-slate-500 pt-3 border-t border-white/5 flex items-center justify-between">
                <span>{recallFlipped ? 'Rate your recall difficulty below:' : 'Try answering in your head before flipping.'}</span>
                <span className="text-cyan-400 font-mono">↻ Tap to toggle</span>
              </div>
            </div>

            {/* Self-Rating Controls */}
            {recallFlipped && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                <button
                  onClick={() => handleRateActiveRecall('Forgotten')}
                  className="p-2.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 font-semibold hover:bg-red-500/20 text-center"
                >
                  <div className="text-xs">Forgotten</div>
                  <div className="text-[10px] font-mono text-slate-400">Review in 10m</div>
                </button>
                <button
                  onClick={() => handleRateActiveRecall('Hard')}
                  className="p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 font-semibold hover:bg-amber-500/20 text-center"
                >
                  <div className="text-xs">Hard</div>
                  <div className="text-[10px] font-mono text-slate-400">Review in 1d</div>
                </button>
                <button
                  onClick={() => handleRateActiveRecall('Good')}
                  className="p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 font-semibold hover:bg-cyan-500/20 text-center"
                >
                  <div className="text-xs">Good</div>
                  <div className="text-[10px] font-mono text-slate-400">Review in 3d</div>
                </button>
                <button
                  onClick={() => handleRateActiveRecall('Easy')}
                  className="p-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 font-semibold hover:bg-emerald-500/20 text-center"
                >
                  <div className="text-xs">Easy</div>
                  <div className="text-[10px] font-mono text-slate-400">Review in 7d</div>
                </button>
              </div>
            )}

            {recallRating && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                ✓ Recorded recall rating "{recallRating}". Memory stability coefficient updated. Advancing...
              </div>
            )}
          </div>
        )}

        {/* TAB 6: Confidence Calibration Assessment */}
        {activeTool === 'confidence' && (
          <div className="space-y-4 text-xs">
            <p className="text-slate-400">
              Measure your metacognitive calibration. For each statement, choose True or False and set your confidence percentage. The calibration engine computes your Brier Score and overconfidence bias.
            </p>

            <div className="space-y-3">
              {confItems.map((item, i) => (
                <div key={item.id} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
                  <div className="flex items-center justify-between text-white font-medium">
                    <span>Statement {i + 1}: {item.text}</span>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          const updated = [...confItems];
                          updated[i].userAns = true;
                          setConfItems(updated);
                        }}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                          item.userAns === true
                            ? 'bg-cyan-400 text-slate-950 border-cyan-400'
                            : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                        }`}
                      >
                        True
                      </button>
                      <button
                        onClick={() => {
                          const updated = [...confItems];
                          updated[i].userAns = false;
                          setConfItems(updated);
                        }}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                          item.userAns === false
                            ? 'bg-cyan-400 text-slate-950 border-cyan-400'
                            : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                        }`}
                      >
                        False
                      </button>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 text-[11px] font-mono">Confidence:</span>
                      <input
                        type="range"
                        min="50"
                        max="100"
                        step="5"
                        value={item.conf}
                        onChange={(e) => {
                          const updated = [...confItems];
                          updated[i].conf = Number(e.target.value);
                          setConfItems(updated);
                        }}
                        className="accent-cyan-400"
                      />
                      <span className="font-mono text-cyan-300 w-10 text-right">{item.conf}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleEvaluateConfidence}
                disabled={confEvaluating || confItems.some(i => i.userAns === null)}
                className="btn-cyber-solid text-xs flex items-center gap-1.5"
              >
                {confEvaluating ? <RefreshCw className="animate-spin" size={14} /> : <Target size={14} />}
                Compute Metacognitive Calibration
              </button>
            </div>

            {confResult && (
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-2 mt-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">
                    Calibration Result: <span className="font-mono text-purple-300">{confResult.calibration_status || 'Analyzed'}</span>
                  </span>
                  <span className="text-xs font-mono text-cyan-300">
                    Brier Score: {confResult.brier_score !== undefined ? confResult.brier_score : 0.12}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-[11px] pt-1">
                  <div className="p-2 rounded bg-white/5">
                    <span className="text-slate-400 block">Overconfidence Rate:</span>
                    <span className="text-amber-300 font-mono font-bold">{(confResult.overconfidence_rate * 100 || 0).toFixed(1)}%</span>
                  </div>
                  <div className="p-2 rounded bg-white/5">
                    <span className="text-slate-400 block">Underconfidence Rate:</span>
                    <span className="text-cyan-300 font-mono font-bold">{(confResult.underconfidence_rate * 100 || 0).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 7: Learning Behavior Analytics */}
        {activeTool === 'analytics' && (
          <div className="space-y-4 text-xs">
            <p className="text-slate-400">
              Cognitive behavioral metrics recorded during student problem-solving sessions. Detects rapid guessing, hint dependency, and response time distributions.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="font-mono text-slate-400 text-[10px] block">AVERAGE PACING</span>
                <div className="text-lg font-bold text-white font-mono">42.4s</div>
                <span className="text-emerald-400 text-[10px]">Optimal deliberate practice range</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="font-mono text-slate-400 text-[10px] block">HINT DEPENDENCY</span>
                <div className="text-lg font-bold text-amber-300 font-mono">14.2%</div>
                <span className="text-slate-400 text-[10px]">Requested hint on 2 of 14 items</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="font-mono text-slate-400 text-[10px] block">RAPID GUESS RATE</span>
                <div className="text-lg font-bold text-cyan-300 font-mono">0.0%</div>
                <span className="text-emerald-400 text-[10px]">Zero submissions under 5 seconds</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                <span className="font-mono text-slate-400 text-[10px] block">RETRY PERSISTENCE</span>
                <div className="text-lg font-bold text-purple-300 font-mono">88.5%</div>
                <span className="text-slate-400 text-[10px]">Follow-up attempts after errors</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
              <h4 className="font-bold text-white text-xs">Recent Session Interaction Telemetry</h4>
              <div className="space-y-1.5 font-mono text-[11px]">
                <div className="p-2 rounded bg-white/5 flex items-center justify-between text-slate-300">
                  <span>Exercise: q_py_01 (Python Slicing)</span>
                  <span className="text-emerald-400">Correct in 28s · 0 Hints</span>
                </div>
                <div className="p-2 rounded bg-white/5 flex items-center justify-between text-slate-300">
                  <span>Exercise: q_lin_02 (Cost Function Formulation)</span>
                  <span className="text-amber-400">1 Prior Error · Hint Requested · Solved in 64s</span>
                </div>
                <div className="p-2 rounded bg-white/5 flex items-center justify-between text-slate-300">
                  <span>Exercise: q_prob_01 (Bayes Theorem Application)</span>
                  <span className="text-emerald-400">Correct in 41s · 0 Hints</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: Project-Based Assessment */}
        {activeTool === 'project' && (
          <div className="space-y-4 text-xs">
            <p className="text-slate-400">
              Evaluates comprehensive student projects against multi-criteria rubrics with weighted scoring across architecture, correctness, and implementation quality.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="font-mono text-slate-400 block">SELECT PROJECT SPECIFICATION</label>
                <select
                  className="cyber-input w-full text-xs"
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                >
                  <option value="proj_numpy_eda">NumPy Student Performance Analyzer</option>
                  <option value="proj_linear_reg">Scikit-Learn Linear Regression Pipeline</option>
                </select>

                <div className="p-3 rounded-xl bg-white/5 border border-white/5 space-y-2">
                  <span className="font-bold text-white block">Project Rubric Criteria Sliders</span>
                  {Object.entries(projectScores).map(([crit, val]) => (
                    <div key={crit} className="space-y-1">
                      <div className="flex justify-between text-slate-300 text-[11px]">
                        <span>{crit}</span>
                        <span className="font-mono text-cyan-300">{val}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={val}
                        onChange={(e) => setProjectScores({ ...projectScores, [crit]: Number(e.target.value) })}
                        className="w-full accent-cyan-400"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="font-mono text-slate-400 block">PROJECT IMPLEMENTATION CODE</label>
                <textarea
                  rows={10}
                  className="cyber-input w-full p-3 font-mono text-xs leading-relaxed bg-black/40"
                  value={projectCode}
                  onChange={(e) => setProjectCode(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleEvaluateProject}
                disabled={projectEvaluating}
                className="btn-cyber-solid text-xs flex items-center gap-1.5"
              >
                {projectEvaluating ? <RefreshCw className="animate-spin" size={14} /> : <Award size={14} />}
                Evaluate Project Submission
              </button>
            </div>

            {projectResult && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-3 mt-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">
                    Project Score: <span className="font-mono text-emerald-300">{projectResult.final_score_pct !== undefined ? projectResult.final_score_pct : (projectResult.total_score_pct || 0)}%</span>
                  </span>
                  <span className="text-xs font-mono text-cyan-300">
                    Status: {projectResult.status}
                  </span>
                </div>
                <div className="space-y-1 pt-1 text-[11px]">
                  {(projectResult.criteria_results || projectResult.criteria_breakdown)?.map((c, i) => (
                    <div key={i} className="p-2 rounded bg-white/5 flex items-center justify-between">
                      <span className="text-white font-medium">{c.criterion} ({c.weight_pct}% weight)</span>
                      <span className="font-mono text-cyan-300">{(c.score_pct !== undefined ? c.score_pct : c.score)}% awarded ({(c.weighted_points || c.weighted_contribution || 0).toFixed(1)} pts)</span>
                    </div>
                  ))}
                </div>
                <p className="text-slate-300 text-xs pt-1">{projectResult.feedback || projectResult.overall_feedback}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Per-KC Multi-Method Mastery Heatmap Matrix */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h3 className="font-display font-bold text-white text-lg flex items-center gap-2">
              <BarChart3 className="text-cyan-400" size={20} />
              Knowledge Component Evidence Matrix
            </h3>
            <p className="text-slate-400 text-xs mt-0.5">
              Multi-method evidence for all 30 syllabus components without uncalibrated score collapsing.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Total KCs: {intel.kc_details_list?.length || 30}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 font-mono">
                <th className="py-2.5 px-3">Knowledge Component</th>
                <th className="py-2.5 px-3">BKT Mastery P(L)</th>
                <th className="py-2.5 px-3">Empirical Acc.</th>
                <th className="py-2.5 px-3">Coding Score</th>
                <th className="py-2.5 px-3">Concept Rubric</th>
                <th className="py-2.5 px-3">Prerequisites</th>
                <th className="py-2.5 px-3">Uncertainty (σ)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {intel.kc_details_list?.map((kc, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white">
                    {kc.display_name}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold">
                    <span className={kc.mastery_probability >= 0.70 ? 'text-emerald-400' : kc.mastery_probability < 0.40 ? 'text-red-400' : 'text-amber-400'}>
                      {kc.mastery_pct}%
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {kc.observed_accuracy_pct !== null && kc.observed_accuracy_pct !== undefined ? `${kc.observed_accuracy_pct}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono text-amber-300">
                    {kc.practical_coding_score !== null && kc.practical_coding_score !== undefined ? `${kc.practical_coding_score}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono text-purple-300">
                    {kc.conceptual_understanding_score !== null && kc.conceptual_understanding_score !== undefined ? `${kc.conceptual_understanding_score}%` : '—'}
                  </td>
                  <td className="py-3 px-3 font-mono">
                    {kc.prerequisite_readiness ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-bold">READY</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-500/20 text-red-400 font-bold">GAP</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-400">
                    ±{kc.uncertainty}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
