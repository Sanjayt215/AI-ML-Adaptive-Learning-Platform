import React, { useState, useEffect } from 'react';
import {
  BookOpen, HelpCircle, Target, FileText, GitBranch, Code2, Award,
  RotateCcw, Activity, RefreshCw, CheckCircle2, AlertTriangle, Sparkles,
  Layers, Clock, ArrowRight, Check, X, ShieldAlert, ChevronRight
} from 'lucide-react';
import { apiFetch } from '../utils/api';

const ASSESSMENT_CATEGORIES = [
  {
    category: 'FOUNDATION',
    description: 'Calibrate initial mastery priors and metacognitive confidence alignment.',
    methods: [
      { id: 'diagnostic', name: '1. Diagnostic Assessment', icon: HelpCircle, difficulty: 'Adaptive', purpose: 'Calibrate BKT prior P(L₀) and detect prerequisite gaps before starting new units.' },
      { id: 'confidence', name: '2. Confidence Calibration', icon: Target, difficulty: 'Metacognitive', purpose: 'Measure subjective probability vs empirical correctness to compute Brier Score and overconfidence bias.' },
    ],
  },
  {
    category: 'UNDERSTANDING',
    description: 'Verify conceptual clarity, mechanisms, and mental graph organization.',
    methods: [
      { id: 'conceptual', name: '3. Conceptual Rubric', icon: FileText, difficulty: 'Intermediate', purpose: 'Score open-ended technical explanations against structured rubrics, detecting misconceptions.' },
      { id: 'concept_map', name: '4. Concept Mapping', icon: GitBranch, difficulty: 'Structural', purpose: 'Connect prerequisite relationships and verify graph alignment against the Curriculum DAG.' },
    ],
  },
  {
    category: 'APPLICATION',
    description: 'Execute runnable Python code in a secure sandbox and evaluate multi-criteria projects.',
    methods: [
      { id: 'coding', name: '5. Practical Coding Sandbox', icon: Code2, difficulty: 'Applied', purpose: 'Execute isolated Python solutions with memory/timeout limits and test case verification.' },
      { id: 'project', name: '6. Project-Based Assessment', icon: Award, difficulty: 'Comprehensive', purpose: 'Evaluate end-to-end data pipelines against weighted multi-criteria rubrics.' },
    ],
  },
  {
    category: 'RETENTION & BEHAVIOUR',
    description: 'Track long-term memory stability and deliberate problem-solving habits.',
    methods: [
      { id: 'active_recall', name: '7. Active Recall', icon: RotateCcw, difficulty: 'Memory', purpose: 'Question-before-answer retrieval practice with 4-button self-rating and interval scheduling.' },
      { id: 'analytics', name: '8. Learning Behaviour Analytics', icon: Activity, difficulty: 'Observational', purpose: 'Analyze deliberate pacing, hint dependency, retry persistence, and rapid guessing.' },
    ],
  },
];

export default function AssessmentsPage() {
  const [activeMethod, setActiveMethod] = useState('diagnostic');

  // State: Diagnostic
  const [diagTopic, setDiagTopic] = useState('linear regression');
  const [diagData, setDiagData] = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagAnswers, setDiagAnswers] = useState({});
  const [diagResult, setDiagResult] = useState(null);

  // State: Confidence
  const [confItems, setConfItems] = useState([
    { id: 1, text: 'In logistic regression, the loss function used is Mean Squared Error.', trueAns: false, userAns: null, conf: 80 },
    { id: 2, text: 'NumPy vectorized operations execute in contiguous C memory without Python pointer chasing.', trueAns: true, userAns: null, conf: 90 },
    { id: 3, text: 'L2 regularization (Ridge) pushes irrelevant weight coefficients exactly to zero.', trueAns: false, userAns: null, conf: 75 },
    { id: 4, text: 'Bayesian Knowledge Tracing models knowledge state as a two-state Hidden Markov Model.', trueAns: true, userAns: null, conf: 85 },
  ]);
  const [confEvaluating, setConfEvaluating] = useState(false);
  const [confResult, setConfResult] = useState(null);

  // State: Conceptual
  const [conceptTopic, setConceptTopic] = useState('python');
  const [conceptPrompt, setConceptPrompt] = useState('Explain how NumPy ndarray differs from standard Python lists in memory layout and vectorization.');
  const [conceptResponse, setConceptResponse] = useState('');
  const [conceptEvaluating, setConceptEvaluating] = useState(false);
  const [conceptResult, setConceptResult] = useState(null);

  // State: Concept Map
  const [mapEdges, setMapEdges] = useState([
    { source: 'python', target: 'data preprocessing', relation: 'prerequisite' },
    { source: 'data preprocessing', target: 'linear regression', relation: 'prerequisite' },
  ]);
  const [newSource, setNewSource] = useState('probability');
  const [newTarget, setNewTarget] = useState('linear regression');
  const [mapEvaluating, setMapEvaluating] = useState(false);
  const [mapResult, setMapResult] = useState(null);

  // State: Coding
  const [codingTopic, setCodingTopic] = useState('python');
  const [codingChallenges, setCodingChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [codeSnippet, setCodeSnippet] = useState('');
  const [codeExecuting, setCodeExecuting] = useState(false);
  const [codeResult, setCodeResult] = useState(null);

  // State: Project
  const [selectedProject, setSelectedProject] = useState('proj_numpy_eda');
  const [projectScores, setProjectScores] = useState({
    'Data Normalization (Min-Max)': 85,
    'Summary Statistics (Mean & Std)': 90,
    'Outlier Detection (Z-Score > 2.0)': 80,
    'Code Quality & Documentation': 95,
  });
  const [projectCode, setProjectCode] = useState(
    'import numpy as np\n\ndef analyze_scores(scores):\n    s_min, s_max = np.min(scores, axis=0), np.max(scores, axis=0)\n    norm = (scores - s_min) / (s_max - s_min + 1e-8)\n    mean = np.mean(norm, axis=0)\n    std = np.std(norm, axis=0)\n    z = (norm - mean) / (std + 1e-8)\n    outliers = np.abs(z) > 2.0\n    return norm, mean, std, outliers'
  );
  const [projectEvaluating, setProjectEvaluating] = useState(false);
  const [projectResult, setProjectResult] = useState(null);

  // State: Active Recall
  const recallDeck = [
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
  ];
  const [recallIdx, setRecallIdx] = useState(0);
  const [recallFlipped, setRecallFlipped] = useState(false);
  const [recallRating, setRecallRating] = useState(null);

  useEffect(() => {
    if (activeMethod === 'coding') {
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
  }, [activeMethod, codingTopic]);

  // Handlers
  const handleLoadDiagnostic = async () => {
    setDiagLoading(true);
    setDiagResult(null);
    setDiagAnswers({});
    try {
      const res = await apiFetch(`/api/assessment/diagnostic/${encodeURIComponent(diagTopic)}`);
      setDiagData(res);
    } catch {
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
        body: JSON.stringify({ topic: diagTopic, answers: diagAnswers }),
      });
      setDiagResult(res);
    } catch (e) {
      setDiagResult({ ok: false, error: e.message });
    }
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

  const handleEvaluateConcept = async () => {
    if (!conceptResponse.trim()) return;
    setConceptEvaluating(true);
    try {
      const res = await apiFetch('/api/assessment/conceptual/evaluate', {
        method: 'POST',
        body: JSON.stringify({ topic: conceptTopic, prompt: conceptPrompt, response: conceptResponse }),
      });
      setConceptResult(res);
    } catch (e) {
      setConceptResult({ ok: false, error: e.message });
    } finally {
      setConceptEvaluating(false);
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

  const handleExecuteCode = async () => {
    if (!selectedChallenge) return;
    setCodeExecuting(true);
    try {
      const res = await apiFetch('/api/assessment/coding/execute', {
        method: 'POST',
        body: JSON.stringify({ code: codeSnippet, test_cases: selectedChallenge.test_cases || [] }),
      });
      setCodeResult(res);
    } catch (e) {
      setCodeResult({ ok: false, error: e.message });
    } finally {
      setCodeExecuting(false);
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

  const handleRateRecall = (rating) => {
    setRecallRating(rating);
    setTimeout(() => {
      setRecallFlipped(false);
      setRecallRating(null);
      setRecallIdx((recallIdx + 1) % recallDeck.length);
    }, 1200);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              UNIFIED ASSESSMENT CENTRE
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-400/10 text-purple-400 border border-purple-400/20">
              8 ASSESSMENT MODALITIES
            </span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">Assessments</h1>
          <p className="text-slate-400 text-sm mt-1">
            Multimodal evaluation measuring conceptual depth, code correctness, graph connections, metacognitive calibration, and retention.
          </p>
        </div>
      </div>

      {/* Two Column Layout: Categories on Left, Active Tool on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {ASSESSMENT_CATEGORIES.map(cat => (
            <div key={cat.category} className="space-y-2">
              <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider font-bold">
                {cat.category}
              </div>
              <div className="space-y-1">
                {cat.methods.map(m => {
                  const Icon = m.icon;
                  const isActive = activeMethod === m.id;
                  return (
                    <button
                      key={m.id}
                      onClick={() => setActiveMethod(m.id)}
                      className={`w-full p-2.5 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                        isActive
                          ? 'bg-cyan-400/15 border-cyan-400 text-white font-bold shadow-sm shadow-cyan-400/10'
                          : 'bg-white/5 border-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <Icon size={14} className={isActive ? 'text-cyan-400' : 'text-slate-400'} />
                        <span className="truncate">{m.name}</span>
                      </div>
                      <ChevronRight size={13} className="text-slate-500 shrink-0" />
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Assessment Active Workspace */}
        <div className="lg:col-span-3 glass-card p-6 space-y-6">
          {/* TAB 1: Diagnostic Assessment */}
          {activeMethod === 'diagnostic' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-cyan-400 uppercase">MODALITY 1 · FOUNDATIONAL CALIBRATION</span>
                <h3 className="font-display font-bold text-white text-lg">Pre-Topic Diagnostic Assessment</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Gauges prior mastery and verifies prerequisite readiness before entering a new syllabus topic.
                </p>
              </div>

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
                  {diagLoading ? <RefreshCw className="animate-spin" size={14} /> : 'Generate Diagnostic Items'}
                </button>
              </div>

              {diagData && diagData.questions && (
                <div className="space-y-4 pt-2">
                  {diagData.questions.map((q, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-white">Item {idx + 1} ({q.diagnostic_role})</span>
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

                  <button onClick={handleSubmitDiagnostic} className="btn-cyber-solid text-xs w-full py-2.5">
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

          {/* TAB 2: Confidence Calibration */}
          {activeMethod === 'confidence' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-purple-400 uppercase">MODALITY 2 · METACOGNITIVE ALIGNMENT</span>
                <h3 className="font-display font-bold text-white text-lg">Confidence & Metacognitive Calibration</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Calculates Brier Score and reveals overconfidence/underconfidence gaps across predictions.
                </p>
              </div>

              <div className="space-y-3">
                {confItems.map((item, i) => (
                  <div key={item.id} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
                    <span className="text-white font-medium block">Statement {i + 1}: {item.text}</span>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            const updated = [...confItems];
                            updated[i].userAns = true;
                            setConfItems(updated);
                          }}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                            item.userAns === true ? 'bg-cyan-400 text-slate-950 border-cyan-400' : 'bg-white/5 border-white/10 text-slate-300'
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
                            item.userAns === false ? 'bg-cyan-400 text-slate-950 border-cyan-400' : 'bg-white/5 border-white/10 text-slate-300'
                          }`}
                        >
                          False
                        </button>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-slate-400 font-mono text-[11px]">Subjective Confidence:</span>
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
                      Status: <span className="font-mono text-purple-300">{confResult.calibration_status}</span>
                    </span>
                    <span className="text-xs font-mono text-cyan-300">
                      Brier Score: {confResult.brier_score !== null && confResult.brier_score !== undefined ? confResult.brier_score : 'N/A'}
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs">{confResult.note}</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Conceptual Rubric */}
          {activeMethod === 'conceptual' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-purple-400 uppercase">MODALITY 3 · NATURAL LANGUAGE RUBRIC</span>
                <h3 className="font-display font-bold text-white text-lg">Conceptual Understanding Assessment</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Natural language explanations graded against multi-criteria rubrics with misconception detection.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-1 space-y-2">
                  <label className="font-mono text-slate-400 block">TOPIC</label>
                  <select
                    className="cyber-input w-full text-xs"
                    value={conceptTopic}
                    onChange={(e) => setConceptTopic(e.target.value)}
                  >
                    <option value="python">Python / NumPy Architecture</option>
                    <option value="linear_regression">Linear Regression Mechanics</option>
                    <option value="classification">Classification Boundaries</option>
                  </select>
                </div>
                <div className="md:col-span-3 space-y-2">
                  <label className="font-mono text-slate-400 block">ASSESSMENT PROMPT</label>
                  <div className="p-2.5 rounded-lg bg-white/5 text-white font-medium">{conceptPrompt}</div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="font-mono text-slate-400 block">NATURAL LANGUAGE EXPLANATION</label>
                <textarea
                  rows={4}
                  className="cyber-input w-full p-3 text-xs leading-relaxed"
                  placeholder="Explain data structures, memory layout, SIMD vectorization, and computational tradeoffs..."
                  value={conceptResponse}
                  onChange={(e) => setConceptResponse(e.target.value)}
                />
              </div>

              <div className="flex justify-end pt-1">
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
                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-3 mt-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">
                      Rubric Score: <span className="font-mono text-purple-300">{conceptResult.score_pct}%</span>
                    </span>
                    <span className="text-[10px] font-mono text-purple-200">
                      Evaluator Confidence: {conceptResult.evaluation_confidence}
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs">{conceptResult.feedback}</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Concept Mapping */}
          {activeMethod === 'concept_map' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-cyan-400 uppercase">MODALITY 4 · STRUCTURAL DEPENDENCIES</span>
                <h3 className="font-display font-bold text-white text-lg">Concept Mapping & Graph Alignment</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Verify prerequisite relationships against the canonical Curriculum DAG.
                </p>
              </div>

              <div className="space-y-2">
                <span className="font-mono text-slate-400 block">ACTIVE CONCEPT EDGES</span>
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
                <button
                  onClick={() => {
                    if (newSource && newTarget && newSource !== newTarget) {
                      setMapEdges([...mapEdges, { source: newSource, target: newTarget, relation: 'prerequisite' }]);
                    }
                  }}
                  className="btn-cyber text-xs py-1 px-3"
                >
                  + Add Edge
                </button>
              </div>

              <div className="flex justify-end pt-1">
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
                    <span className="text-emerald-400 text-xs font-bold">{mapResult.valid_edges_count} Valid Edges</span>
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

          {/* TAB 5: Practical Coding */}
          {activeMethod === 'coding' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-amber-400 uppercase">MODALITY 5 · SANDBOXED EXECUTION</span>
                <h3 className="font-display font-bold text-white text-lg">Practical Coding Sandbox</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Subprocess-isolated Python environment verifying syntax, unit test cases, and runtime efficiency.
                </p>
              </div>

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

              <div className="space-y-1.5">
                <label className="font-mono text-slate-400 block">PYTHON SOLUTION CODE</label>
                <textarea
                  rows={6}
                  className="cyber-input w-full p-3 font-mono text-xs leading-relaxed bg-black/40"
                  value={codeSnippet}
                  onChange={(e) => setCodeSnippet(e.target.value)}
                />
              </div>

              <div className="flex justify-end pt-1">
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

          {/* TAB 6: Project-Based Assessment */}
          {activeMethod === 'project' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-emerald-400 uppercase">MODALITY 6 · COMPREHENSIVE RUBRIC</span>
                <h3 className="font-display font-bold text-white text-lg">Project-Based Practical Assessment</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Multi-criterion weighted scoring evaluating architecture, data transformation, and code quality.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <label className="font-mono text-slate-400 block">PROJECT SPECIFICATION</label>
                  <select
                    className="cyber-input w-full text-xs"
                    value={selectedProject}
                    onChange={(e) => setSelectedProject(e.target.value)}
                  >
                    <option value="proj_numpy_eda">NumPy Student Performance Analyzer</option>
                    <option value="proj_linear_reg">Scikit-Learn Linear Regression Pipeline</option>
                  </select>

                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-2.5">
                    <span className="font-bold text-white block">Achievement Rubric Sliders</span>
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
                  <label className="font-mono text-slate-400 block">PROJECT PYTHON IMPLEMENTATION</label>
                  <textarea
                    rows={9}
                    className="cyber-input w-full p-3 font-mono text-xs leading-relaxed bg-black/40"
                    value={projectCode}
                    onChange={(e) => setProjectCode(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex justify-end pt-1">
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
                      Total Project Score: <span className="font-mono text-emerald-300">{projectResult.final_score_pct}% (Grade: {projectResult.grade})</span>
                    </span>
                    <span className="text-xs font-mono text-cyan-300">Status: {projectResult.status}</span>
                  </div>
                  <div className="space-y-1 pt-1 text-[11px]">
                    {projectResult.criteria_results?.map((c, i) => (
                      <div key={i} className="p-2 rounded bg-white/5 flex items-center justify-between">
                        <span className="text-white font-medium">{c.criterion} ({c.weight_pct}% weight)</span>
                        <span className="font-mono text-cyan-300">{c.score_pct}% awarded ({c.weighted_points} pts)</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-slate-300 text-xs pt-1">{projectResult.feedback}</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 7: Active Recall */}
          {activeMethod === 'active_recall' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-purple-400 uppercase">MODALITY 7 · ACTIVE RETRIEVAL PRACTICE</span>
                <h3 className="font-display font-bold text-white text-lg">Active Recall Flashcards</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Question-before-answer flashcard testing with 4-button self-rating and interval scheduling.
                </p>
              </div>

              <div
                onClick={() => setRecallFlipped(!recallFlipped)}
                className="p-6 rounded-2xl bg-slate-900 border border-white/10 min-h-[180px] flex flex-col justify-between cursor-pointer hover:border-cyan-400/40 transition-all shadow-lg"
              >
                <div>
                  <div className="flex items-center justify-between text-slate-400 text-[11px] mb-3">
                    <span className="font-mono font-bold text-cyan-400">{recallDeck[recallIdx].concept}</span>
                    <span>{recallFlipped ? 'Answer Revealed' : 'Click card to flip'}</span>
                  </div>
                  <div className="text-white text-sm font-medium leading-relaxed">
                    {recallFlipped ? recallDeck[recallIdx].answer : recallDeck[recallIdx].question}
                  </div>
                </div>

                <div className="text-[11px] text-slate-500 pt-3 border-t border-white/5 flex items-center justify-between">
                  <span>{recallFlipped ? 'Rate your recall difficulty below:' : 'Try answering in your head before flipping.'}</span>
                  <span className="text-cyan-400 font-mono">↻ Tap to flip</span>
                </div>
              </div>

              {recallFlipped && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                  <button
                    onClick={() => handleRateRecall('Forgotten')}
                    className="p-2.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 font-semibold hover:bg-red-500/20 text-center"
                  >
                    <div className="text-xs">Forgotten</div>
                    <div className="text-[10px] font-mono text-slate-400">Review in 10m</div>
                  </button>
                  <button
                    onClick={() => handleRateRecall('Hard')}
                    className="p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 font-semibold hover:bg-amber-500/20 text-center"
                  >
                    <div className="text-xs">Hard</div>
                    <div className="text-[10px] font-mono text-slate-400">Review in 1d</div>
                  </button>
                  <button
                    onClick={() => handleRateRecall('Good')}
                    className="p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 font-semibold hover:bg-cyan-500/20 text-center"
                  >
                    <div className="text-xs">Good</div>
                    <div className="text-[10px] font-mono text-slate-400">Review in 3d</div>
                  </button>
                  <button
                    onClick={() => handleRateRecall('Easy')}
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

          {/* TAB 8: Learning Analytics */}
          {activeMethod === 'analytics' && (
            <div className="space-y-4 text-xs">
              <div className="border-b border-white/10 pb-3">
                <span className="text-[10px] font-mono text-cyan-400 uppercase">MODALITY 8 · BEHAVIOURAL OBSERVATIONS</span>
                <h3 className="font-display font-bold text-white text-lg">Learning Behaviour Analytics</h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Cognitive behavioural telemetry tracking deliberate pacing, hint dependency, and retry persistence.
                </p>
              </div>

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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
