import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, Cell,
} from 'recharts';
import {
  LayoutDashboard, TrendingUp, Brain, BookOpen, Zap, Target,
  ArrowRight, Info, ChevronRight, Cpu, Database, Star, Sparkles, RefreshCw,
  Award, CheckCircle2, XCircle, RotateCcw, AlertTriangle, ShieldCheck, Play
} from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import { apiFetch } from '../utils/api';
import StatCard from '../components/StatCard';
import HeatmapGrid from '../components/HeatmapGrid';
import ProgressRing from '../components/ProgressRing';
import KCDetailModal from '../components/KCDetailModal';
import AssessmentModal from '../components/AssessmentModal';
import RevisionSection from '../components/RevisionSection';
import ResearchLabSection from '../components/ResearchLabSection';

const LEVEL_CONFIG = {
  advanced:     { label: 'Advanced',     color: '#f87171', bg: 'bg-red-400/10',    border: 'border-red-400/30',    ring: '#f87171' },
  intermediate: { label: 'Intermediate', color: '#fbbf24', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', ring: '#fbbf24' },
  beginner:     { label: 'Beginner',     color: '#4ade80', bg: 'bg-green-400/10',  border: 'border-green-400/30',  ring: '#4ade80' },
};

export default function DashboardPage() {
  const {
    assessment, profile, modelScores, dataInfo,
    modelName, automlEngine, avgScore,
    strengths, weakTopics, accuracyTrend, topicMastery, modernFeatures, learningScore, aiFeatures, mlFeatures, datasetRegistry, llmMode, datasetSources,
    bktMastery: initialBktMastery, refresh: refreshFlaskContext
  } = useFlaskData();

  const [activeTab, setActiveTab] = useState('overview');
  const [selectedStrategy, setSelectedStrategy] = useState('composite_adaptive');

  // Adaptive Recommendation States
  const [recommendation, setRecommendation] = useState(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState('');

  // Interactive Practice on Recommendation Card
  const [selectedPracticeOpt, setSelectedPracticeOpt] = useState('');
  const [submittingPractice, setSubmittingPractice] = useState(false);
  const [practiceFeedback, setPracticeFeedback] = useState(null);
  const [practiceStartTime, setPracticeStartTime] = useState(Date.now());

  // BKT & Curriculum States
  const [liveBktMastery, setLiveBktMastery] = useState(null);
  const [curriculumPlan, setCurriculumPlan] = useState(null);
  const [curriculumLoading, setCurriculumLoading] = useState(false);
  const [curriculumError, setCurriculumError] = useState('');

  // Assessment & Revision States
  const [isAssessmentOpen, setIsAssessmentOpen] = useState(false);
  const [assessmentHistory, setAssessmentHistory] = useState([]);
  const [assessmentComparison, setAssessmentComparison] = useState(null);
  const [selectedKCForModal, setSelectedKCForModal] = useState(null);

  const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';

  const fetchBktMastery = async () => {
    try {
      const data = await apiFetch(`/api/learning/mastery/${learnerId}`);
      if (data && data.ok) {
        setLiveBktMastery(data);
      }
    } catch (err) {
      console.warn('Could not load live BKT mastery:', err);
    }
  };

  const fetchCurriculumPlan = async () => {
    setCurriculumLoading(true);
    setCurriculumError('');
    try {
      const data = await apiFetch(`/api/curriculum/plan?learner_id=${learnerId}`);
      if (data && data.ok) {
        setCurriculumPlan(data);
      }
    } catch (err) {
      setCurriculumError(err.message || 'Could not load curriculum plan');
    } finally {
      setCurriculumLoading(false);
    }
  };

  const fetchRecommendation = async (strategyOverride, topicOverride) => {
    setRecLoading(true);
    setRecError('');
    setSelectedPracticeOpt('');
    setPracticeFeedback(null);
    setPracticeStartTime(Date.now());
    try {
      const strat = strategyOverride || selectedStrategy;
      let url = `/api/adaptive/recommendation?learner_id=${learnerId}&strategy=${strat}`;
      if (topicOverride) {
        url += `&topic=${encodeURIComponent(topicOverride)}`;
      }
      const data = await apiFetch(url);
      if (data && data.ok) {
        setRecommendation(data);
      } else {
        throw new Error(data?.error || 'Failed to fetch recommendation.');
      }
    } catch (err) {
      setRecError(err.message || 'Could not load recommendation');
    } finally {
      setRecLoading(false);
    }
  };

  const fetchAssessments = async () => {
    try {
      const histData = await apiFetch(`/api/assessment/history/${learnerId}`);
      if (histData && histData.ok) {
        setAssessmentHistory(histData.assessments || []);
      }
      const compData = await apiFetch(`/api/assessment/compare/${learnerId}`);
      if (compData && compData.ok) {
        setAssessmentComparison(compData.comparison);
      }
    } catch (err) {
      console.warn('Assessment history fetch warning:', err);
    }
  };

  useEffect(() => {
    fetchBktMastery();
    fetchCurriculumPlan();
    fetchRecommendation();
    fetchAssessments();
  }, []);

  const handleStrategyChange = (newStrategy) => {
    setSelectedStrategy(newStrategy);
    fetchRecommendation(newStrategy);
  };

  // Submit in-place practice answer
  const handleSubmitPractice = async () => {
    if (!selectedPracticeOpt || !recommendation) return;
    setSubmittingPractice(true);
    const elapsed = Date.now() - practiceStartTime;
    try {
      const res = await apiFetch('/api/practice/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: learnerId,
          item_id: recommendation.item_id,
          selected_option: selectedPracticeOpt,
          response_time_ms: Math.max(elapsed, 500),
        }),
      });

      if (res && res.ok) {
        setPracticeFeedback(res);
        // Refresh BKT and curriculum plan immediately
        fetchBktMastery();
        fetchCurriculumPlan();
        refreshFlaskContext();
      } else {
        throw new Error(res?.error || 'Failed to evaluate practice answer.');
      }
    } catch (err) {
      alert('Error submitting practice answer: ' + err.message);
    } finally {
      setSubmittingPractice(false);
    }
  };

  const currentBkt = liveBktMastery || initialBktMastery;
  const overallLevel = avgScore >= 75 ? 'advanced' : avgScore >= 45 ? 'intermediate' : 'beginner';
  const lvlCfg = LEVEL_CONFIG[overallLevel];
  const radarData = topicMastery.map(t => ({ subject: t.topic, A: t.mastery, fullMark: 100 }));

  // Calculate mastered KCs count
  const masteredCount = (currentBkt?.topics || []).filter(t => (t.mastery_pct || (t.mastery_probability * 100)) >= 80).length;
  const assessedCount = (currentBkt?.topics || []).filter(t => t.status === 'assessed').length;

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">

      {/* Top Header Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="font-display font-bold text-2xl text-white">Adaptive Student Dashboard</h1>
            <span className={`badge-chip border ${lvlCfg.bg} ${lvlCfg.border}`} style={{ color: lvlCfg.color }}>
              {lvlCfg.label}
            </span>
          </div>
          <p className="text-slate-400 text-xs">
            Learner: <span className="font-mono text-cyan-400">{learnerId}</span> · 
            Goal: <span className="text-slate-200">{profile?.target_goal || 'Full Adaptive Machine Learning Curriculum'}</span>
          </p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => setIsAssessmentOpen(true)}
            className="btn-cyber text-xs flex items-center gap-1.5 py-2 px-3.5 border-purple-400/40 text-purple-300 hover:border-purple-400"
          >
            <Award size={14} /> Diagnostic Assessment
          </button>
          <Link to="/path" className="btn-cyber text-xs flex items-center gap-1.5 py-2 px-3">
            <BookOpen size={14} /> Prerequisite DAG
          </Link>
          <button
            onClick={() => {
              localStorage.removeItem('autolearn_learner_id');
              window.location.reload();
            }}
            className="btn-cyber text-xs text-red-400 border-red-400/30 hover:border-red-400/60 py-2 px-3"
            title="Switch or reset pseudonymous learner ID"
          >
            Reset Learner
          </button>
        </div>
      </div>

      {/* Primary Empirical Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        <StatCard icon={TrendingUp} label="Avg Quiz Score" value={`${avgScore}%`} color="cyan" />
        <StatCard icon={Brain} label="Assessed KCs" value={`${assessedCount} / ${currentBkt?.topics?.length || 30}`} color="purple" sub="Observable practice" />
        <StatCard icon={CheckCircle2} label="Mastered KCs" value={`${masteredCount}`} color="green" sub="P(K) ≥ 80%" />
        <StatCard icon={Target} label="Frontier Ready" value={`${curriculumPlan?.curriculum_summary?.ready_frontier || 1}`} color="cyan" sub="Prerequisites met" />
        <StatCard icon={Cpu} label="Active Policy" value="composite" color="green" sub="Rule-constrained KT" />
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-1 p-1 glass-card w-fit flex-wrap">
        {[
          'overview',
          'analytics',
          'topics',
          'knowledge tracing',
          'curriculum',
          'revision',
          'assessment',
          'research lab',
          'model'
        ].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-display font-medium transition-all capitalize ${
              activeTab === tab
                ? 'bg-cyan-400/15 text-cyan-400 border border-cyan-400/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">

          {/* Real-Time Interactive Adaptive Exercise Card (Phase E) */}
          <div className="glass-card p-6 border-cyan-400/30 relative overflow-hidden">
            <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
              <div className="flex items-center gap-2.5">
                <Sparkles size={20} className="text-cyan-400 animate-pulse" />
                <div>
                  <h3 className="font-display font-semibold text-white text-base">Adaptive Practice Recommendation</h3>
                  <p className="text-slate-400 text-xs">
                    Dynamically recommended via multi-objective pedagogical optimization
                  </p>
                </div>
              </div>

              {/* Strategy Selector & Refresh */}
              <div className="flex items-center gap-2">
                <select
                  value={selectedStrategy}
                  onChange={e => handleStrategyChange(e.target.value)}
                  className="cyber-input text-xs py-1.5 px-2 bg-dark-400 border-white/10 text-slate-300"
                >
                  <option value="composite_adaptive">Composite Adaptive (Production)</option>
                  <option value="prereq_aware_weakest">Prerequisite-Aware Weakest</option>
                  <option value="forgetting_revision">Forgetting-Aware Revision</option>
                  <option value="confidence_exploration">Confidence Exploration</option>
                  <option value="frustration_remedial">Frustration Remedial</option>
                </select>
                <button
                  onClick={() => fetchRecommendation()}
                  disabled={recLoading}
                  className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3"
                >
                  <RefreshCw size={12} className={recLoading ? 'animate-spin' : ''} />
                  Refresh
                </button>
              </div>
            </div>

            {recLoading && (
              <div className="py-8 text-center text-slate-400 text-sm animate-pulse">
                Evaluating learner state across Bayesian Knowledge Tracing & pedagogical policies...
              </div>
            )}

            {recError && !recLoading && (
              <div className="p-4 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300 text-xs">
                {recError}
              </div>
            )}

            {!recLoading && !recError && recommendation && (
              <div className="space-y-4">
                {/* Pedagogical Rationale Banner */}
                <div className="p-3.5 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-xs text-slate-300 leading-relaxed">
                  <div className="text-cyan-400 font-semibold mb-1 flex items-center gap-1.5">
                    <Info size={14} /> Pedagogical Rationale:
                  </div>
                  {recommendation.explanation?.pedagogical_rationale}
                </div>

                {/* Question & Interactive Options Card */}
                <div className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-4">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className="text-white font-display font-bold text-base capitalize">
                      {recommendation.topic?.replace(/_/g, ' ')} — Difficulty {recommendation.difficulty}/5
                    </span>
                    <span className="text-xs font-mono text-purple-300 bg-purple-400/10 px-2.5 py-1 rounded-md border border-purple-400/20">
                      ID: {recommendation.item_id}
                    </span>
                  </div>

                  <p className="text-slate-100 text-sm font-medium leading-relaxed">
                    {recommendation.question}
                  </p>

                  {/* Interactive Option Buttons */}
                  <div className="space-y-2 pt-1">
                    {(recommendation.options || []).map((opt, i) => {
                      const isSelected = selectedPracticeOpt === opt;
                      return (
                        <button
                          key={i}
                          type="button"
                          onClick={() => !practiceFeedback && setSelectedPracticeOpt(opt)}
                          disabled={!!practiceFeedback}
                          className={`w-full p-3 rounded-xl border text-left text-xs transition flex items-center justify-between ${
                            isSelected
                              ? 'bg-cyan-400/20 border-cyan-400 text-white font-semibold'
                              : 'bg-white/4 border-white/8 text-slate-300 hover:bg-white/8 hover:border-white/20'
                          }`}
                        >
                          <span>{opt}</span>
                          {isSelected && <CheckCircle2 size={14} className="text-cyan-400 flex-shrink-0" />}
                        </button>
                      );
                    })}
                  </div>

                  {/* Submit / Feedback Controls */}
                  <div className="pt-2 flex items-center justify-between flex-wrap gap-3">
                    <div className="text-xs text-slate-400">
                      {!practiceFeedback && (
                        <span>Select your answer and submit to update latent BKT mastery in real-time.</span>
                      )}
                    </div>

                    {!practiceFeedback ? (
                      <button
                        onClick={handleSubmitPractice}
                        disabled={!selectedPracticeOpt || submittingPractice}
                        className="btn-cyber text-xs py-2 px-5 bg-cyan-400 text-dark-300 font-bold border-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {submittingPractice ? 'Evaluating...' : 'Submit Answer'}
                      </button>
                    ) : (
                      <button
                        onClick={() => fetchRecommendation()}
                        className="btn-cyber text-xs flex items-center gap-1.5 py-2 px-4 bg-cyan-400/20 border-cyan-400 text-cyan-300"
                      >
                        Next Recommended Exercise <ArrowRight size={14} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Instant Feedback Alert */}
                {practiceFeedback && (
                  <div className={`p-4 rounded-xl border text-xs space-y-1.5 animate-fade-in ${
                    practiceFeedback.is_correct
                      ? 'bg-green-400/10 border-green-400/30 text-green-300'
                      : 'bg-red-400/10 border-red-400/30 text-red-300'
                  }`}>
                    <div className="flex items-center gap-2 font-display font-bold text-sm">
                      {practiceFeedback.is_correct ? (
                        <>
                          <CheckCircle2 size={16} className="text-green-400" />
                          <span>Correct! Well done.</span>
                        </>
                      ) : (
                        <>
                          <XCircle size={16} className="text-red-400" />
                          <span>Incorrect.</span>
                        </>
                      )}
                    </div>
                    {!practiceFeedback.is_correct && (
                      <div className="text-slate-300">
                        The correct answer was: <strong className="text-white font-mono">{practiceFeedback.correct_answer}</strong>
                      </div>
                    )}
                    <div className="text-[11px] text-slate-400 pt-1">
                      Learner interaction logged to SQLite interaction store. Bayesian Knowledge Tracing posterior belief updated.
                    </div>
                  </div>
                )}

                {/* 4 Pedagogical Diagnostics Pillars */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="glass-card p-2.5">
                    <span className="text-slate-500 block">Topic Mastery P(K)</span>
                    <span className="font-mono text-cyan-400 font-bold">
                      {Math.round((recommendation.explanation?.topic_mastery || 0) * 100)}%
                    </span>
                  </div>
                  <div className="glass-card p-2.5">
                    <span className="text-slate-500 block">Predicted Retention</span>
                    <span className="font-mono text-green-400 font-bold">
                      {Math.round((recommendation.explanation?.predicted_retention || 0) * 100)}%
                    </span>
                  </div>
                  <div className="glass-card p-2.5">
                    <span className="text-slate-500 block">Evidence Confidence</span>
                    <span className="font-mono text-purple-400 font-bold capitalize">
                      {recommendation.explanation?.evidence_quality || 'unassessed'}
                    </span>
                  </div>
                  <div className="glass-card p-2.5">
                    <span className="text-slate-500 block">Frustration Risk</span>
                    <span className="font-mono text-yellow-400 font-bold capitalize">
                      {recommendation.explanation?.frustration_risk || 'low'}
                    </span>
                  </div>
                </div>

              </div>
            )}
          </div>

          {/* Level Ring + Topic Assessment Summary Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-card p-6 flex flex-col items-center gap-4">
              <div className="font-display font-semibold text-white text-sm w-full">Empirical Mastery Overview</div>
              <ProgressRing
                value={avgScore}
                size={130}
                stroke={10}
                color={lvlCfg.ring}
                label={lvlCfg.label}
                sublabel={`${avgScore}% avg score`}
              />
              <div className="w-full space-y-2">
                {assessment.slice(0, 6).map(item => {
                  const cfg = LEVEL_CONFIG[item.predicted_level] || LEVEL_CONFIG.beginner;
                  return (
                    <div key={item.topic} className="flex items-center gap-2">
                      <div className="flex-1 text-xs text-slate-400 capitalize">{item.topic}</div>
                      <div className="w-24 difficulty-track">
                        <div className="difficulty-fill" style={{ width: `${item.score_pct}%`, background: cfg.color }} />
                      </div>
                      <div className="w-8 text-right font-mono text-xs" style={{ color: cfg.color }}>{item.score_pct}%</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Assessment results table */}
            <div className="lg:col-span-2 glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="font-display font-semibold text-white text-sm">Observed Quiz Performance by Topic</div>
                <Link to="/quiz" className="btn-cyber text-xs py-1 px-3">Open Full Quiz</Link>
              </div>

              {assessment.length === 0 ? (
                <div className="py-12 text-center space-y-3">
                  <BookOpen size={32} className="text-slate-500 mx-auto" />
                  <div className="text-white font-medium text-sm">No Topic Quiz Data Yet</div>
                  <p className="text-slate-400 text-xs max-w-sm mx-auto">
                    Take your first diagnostic quiz or start adaptive practice above to measure observed topic performance.
                  </p>
                  <Link to="/quiz" className="btn-cyber text-xs inline-flex items-center gap-1.5 py-2 px-4">
                    Take Adaptive Quiz <ArrowRight size={14} />
                  </Link>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="cyber-table">
                    <thead>
                      <tr>
                        <th className="text-left">Topic</th>
                        <th className="text-left">Score</th>
                        <th className="text-left">Predicted Level</th>
                        <th className="text-left">Exam Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assessment.map(item => {
                        const cfg = LEVEL_CONFIG[item.predicted_level] || LEVEL_CONFIG.beginner;
                        return (
                          <tr key={item.topic}>
                            <td className="font-display font-medium text-white capitalize">{item.topic}</td>
                            <td>
                              <div className="flex items-center gap-2">
                                <div className="w-16 difficulty-track">
                                  <div className="difficulty-fill" style={{ width: `${item.score_pct}%`, background: cfg.color }} />
                                </div>
                                <span className="font-mono text-xs" style={{ color: cfg.color }}>{item.score_pct}%</span>
                              </div>
                            </td>
                            <td>
                              <span className={`badge-chip border ${cfg.bg} ${cfg.border}`} style={{ color: cfg.color }}>
                                {item.predicted_level}
                              </span>
                            </td>
                            <td className="font-mono text-cyan-400">{item.predicted_exam_score}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

        </div>
      )}

      {/* ── ANALYTICS TAB ── */}
      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-1">Accuracy Trend</div>
            <div className="text-slate-500 text-xs mb-5">Daily quiz accuracy vs target</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={accuracyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} width={28} />
                <Tooltip />
                <Line type="monotone" dataKey="accuracy" stroke="#00d4ff" strokeWidth={2.5} dot={{ fill: '#00d4ff', r: 4, strokeWidth: 0 }} name="Accuracy" activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="target" stroke="rgba(168,85,247,0.4)" strokeWidth={1.5} strokeDasharray="5 5" dot={false} name="Target" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-1">Topic Mastery</div>
            <div className="text-slate-500 text-xs mb-5">Observed performance per topic</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={topicMastery} barSize={24}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="topic" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip />
                <Bar dataKey="mastery" name="Mastery" radius={[6, 6, 0, 0]}>
                  {topicMastery.map((entry, i) => (
                    <Cell key={i} fill={entry.mastery >= 75 ? '#4ade80' : entry.mastery >= 50 ? '#fbbf24' : entry.mastery >= 30 ? '#fb923c' : '#f87171'} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-card p-6 lg:col-span-2">
            <div className="font-display font-semibold text-white text-sm mb-1">Knowledge Radar Coverage</div>
            <div className="text-slate-500 text-xs mb-4">Multi-dimensional knowledge coverage</div>
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Space Grotesk' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569', fontSize: 9 }} />
                <Radar name="Mastery" dataKey="A" stroke="#00d4ff" fill="#00d4ff" fillOpacity={0.12} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── TOPICS TAB (Heatmap) ── */}
      {activeTab === 'topics' && (
        <div className="glass-card p-6">
          <div className="font-display font-semibold text-white text-sm mb-1">Weak Topic Heatmap</div>
          <div className="text-slate-500 text-xs mb-6">Hover a cell for details. Color = observed mastery level.</div>
          <HeatmapGrid assessment={assessment} />
        </div>
      )}

      {/* ── KNOWLEDGE TRACING TAB (BKT Engine, Phase C) ── */}
      {activeTab === 'knowledge tracing' && (
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-4 mb-2">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Brain size={18} className="text-cyan-400" />
                <h2 className="font-display font-semibold text-white text-base">Bayesian Knowledge Tracing (BKT) Latent State</h2>
              </div>
              <p className="text-slate-400 text-xs">
                Estimated latent mastery probability <span className="font-mono text-cyan-400">P(K)</span> updated sequentially after each response.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="badge-chip border border-white/10 text-slate-400 text-xs font-mono">
                Model: {currentBkt?.model || 'BKT'} · {currentBkt?.parameter_version || 'bkt-heuristic-v1'}
              </span>
              <button
                onClick={fetchBktMastery}
                className="btn-cyber text-xs py-1 px-2.5 flex items-center gap-1"
              >
                <RefreshCw size={11} /> Refresh BKT
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-purple-400/10 border border-purple-400/20 text-xs text-slate-300 leading-relaxed">
            <span className="text-purple-300 font-semibold">BKT Heuristic Parameters: </span>
            Initialized with standard baseline priors (<span className="font-mono text-white">P(L₀)=0.20, P(T)=0.15, P(G)=0.20, P(S)=0.10</span>).
            Unpracticed topics are explicitly marked <span className="text-slate-400 font-semibold">Not assessed</span> rather than assumed mastered.
            Click any row to inspect parameters and practice that concept.
          </div>

          <div className="overflow-x-auto">
            <table className="cyber-table">
              <thead>
                <tr>
                  <th className="text-left">Knowledge Component (KC)</th>
                  <th className="text-left">Status</th>
                  <th className="text-left">Estimated Mastery P(K)</th>
                  <th className="text-left">Evidence / Answers</th>
                  <th className="text-left">Evidence Quality</th>
                  <th className="text-left">Action</th>
                </tr>
              </thead>
              <tbody>
                {(currentBkt?.topics || []).map(kc => {
                  const isAssessed = kc.status === 'assessed';
                  const pct = kc.mastery_pct ?? Math.round(kc.mastery_probability * 100);
                  const color = !isAssessed ? '#94a3b8' : pct >= 75 ? '#4ade80' : pct >= 50 ? '#fbbf24' : '#f87171';
                  return (
                    <tr
                      key={kc.kc_id}
                      onClick={() => setSelectedKCForModal(kc)}
                      className="cursor-pointer hover:bg-white/5 transition"
                    >
                      <td className="font-display font-medium text-white capitalize">{kc.kc_id?.replace(/_/g, ' ')}</td>
                      <td>
                        <span className={`badge-chip border ${isAssessed ? 'bg-cyan-400/10 border-cyan-400/30 text-cyan-400' : 'bg-slate-400/10 border-slate-400/20 text-slate-400'}`}>
                          {isAssessed ? 'Assessed' : 'Not assessed'}
                        </span>
                      </td>
                      <td>
                        {isAssessed ? (
                          <div className="flex items-center gap-2">
                            <div className="w-20 difficulty-track">
                              <div className="difficulty-fill" style={{ width: `${pct}%`, background: color }} />
                            </div>
                            <span className="font-mono text-xs font-semibold" style={{ color }}>{pct}%</span>
                          </div>
                        ) : (
                          <span className="font-mono text-xs text-slate-500">— (prior: {Math.round(kc.prior_probability * 100)}%)</span>
                        )}
                      </td>
                      <td className="font-mono text-xs">
                        {isAssessed ? (
                          <span>
                            <span className="text-green-400">{kc.correct_count} correct</span> / <span className="text-red-400">{kc.incorrect_count} incorrect</span> ({kc.observation_count} total)
                          </span>
                        ) : (
                          <span className="text-slate-500">0 answers</span>
                        )}
                      </td>
                      <td>
                        <span className={`text-xs capitalize font-medium ${kc.evidence_quality === 'solid' ? 'text-green-400' : kc.evidence_quality === 'moderate' ? 'text-yellow-400' : kc.evidence_quality === 'limited' ? 'text-orange-400' : 'text-slate-500'}`}>
                          {kc.evidence_quality || 'none'}
                        </span>
                      </td>
                      <td>
                        <span className="text-cyan-400 hover:text-cyan-300 text-xs font-medium flex items-center gap-1">
                          Inspect <ChevronRight size={12} />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── CURRICULUM TAB (Phase D) ── */}
      {activeTab === 'curriculum' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="font-display font-semibold text-white text-base mb-1">Prerequisite DAG Curriculum Plan</h3>
              <p className="text-slate-400 text-xs">
                Target Goal: <span className="text-cyan-400 font-mono">{curriculumPlan?.target_goal || 'full_curriculum'}</span> · 
                Mastery Threshold: <span className="text-white font-mono">{Math.round((curriculumPlan?.mastery_target_threshold || 0.8) * 100)}%</span>
              </p>
            </div>
            <button
              onClick={fetchCurriculumPlan}
              disabled={curriculumLoading}
              className="btn-cyber text-xs flex items-center gap-1.5 py-1.5 px-3"
            >
              <RefreshCw size={12} className={curriculumLoading ? 'animate-spin' : ''} />
              Refresh Plan
            </button>
          </div>

          {curriculumLoading && (
            <div className="py-8 text-center text-slate-400 text-sm animate-pulse">
              Evaluating prerequisite DAG topological order and active frontier...
            </div>
          )}

          {curriculumError && !curriculumLoading && (
            <div className="p-4 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300 text-xs">
              {curriculumError}
            </div>
          )}

          {!curriculumLoading && !curriculumError && curriculumPlan && (
            <div className="space-y-6">
              {/* Summary counters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="glass-card p-3">
                  <span className="text-slate-500 block">Total Syllabus KCs</span>
                  <span className="font-mono text-white text-lg font-bold">{curriculumPlan.curriculum_summary?.total_topics || 30}</span>
                </div>
                <div className="glass-card p-3">
                  <span className="text-slate-500 block">Mastered KCs (≥ 80%)</span>
                  <span className="font-mono text-green-400 text-lg font-bold">{curriculumPlan.curriculum_summary?.mastered || 0}</span>
                </div>
                <div className="glass-card p-3">
                  <span className="text-slate-500 block">Ready Frontier KCs</span>
                  <span className="font-mono text-cyan-400 text-lg font-bold">{curriculumPlan.curriculum_summary?.ready_frontier || 1}</span>
                </div>
                <div className="glass-card p-3">
                  <span className="text-slate-500 block">Locked (Prereqs Pending)</span>
                  <span className="font-mono text-slate-500 text-lg font-bold">{curriculumPlan.curriculum_summary?.locked || 29}</span>
                </div>
              </div>

              {/* 4 Progression Stages */}
              <div className="space-y-4">
                <h4 className="font-display font-semibold text-white text-sm">Curriculum Progression Stages</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(curriculumPlan.stages || []).map(stage => (
                    <div key={stage.stage_number} className="p-4 rounded-xl bg-white/4 border border-white/8 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-display font-bold text-white text-sm">{stage.stage_title}</span>
                        <span className="badge-chip border border-white/10 text-slate-400 text-xs">
                          {stage.topics?.length || 0} Topics
                        </span>
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {stage.topics?.map(t => (
                          <div
                            key={t.topic}
                            onClick={() => setSelectedKCForModal(t)}
                            className="flex items-center justify-between text-xs py-1.5 px-2 rounded-lg hover:bg-white/5 cursor-pointer border-b border-white/5 transition"
                          >
                            <span className="capitalize text-slate-300 font-medium">{t.topic.replace(/_/g, ' ')}</span>
                            <div className="flex items-center gap-2">
                              <span className={`badge-chip text-[10px] ${
                                t.status === 'mastered'
                                  ? 'text-green-400 bg-green-400/10'
                                  : t.status === 'ready'
                                  ? 'text-cyan-400 bg-cyan-400/10'
                                  : t.status === 'in_progress'
                                  ? 'text-yellow-400 bg-yellow-400/10'
                                  : 'text-slate-500 bg-white/5'
                              }`}>
                                {t.status}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400">{Math.round(t.current_mastery * 100)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}
        </div>
      )}

      {/* ── REVISION TAB (Spaced Repetition, Phase F) ── */}
      {activeTab === 'revision' && (
        <RevisionSection
          onSelectPractice={(topic) => {
            fetchRecommendation(undefined, topic);
            setActiveTab('overview');
          }}
        />
      )}

      {/* ── ASSESSMENT TAB (Diagnostic Pre/Post, Phase G) ── */}
      {activeTab === 'assessment' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="font-display font-semibold text-white text-base mb-1">Diagnostic Pre/Post Assessment System</h3>
              <p className="text-slate-400 text-xs">
                Independent unassisted test evaluation · Hake's normalized gain measurement ($g_{norm}$)
              </p>
            </div>
            <button
              onClick={() => setIsAssessmentOpen(true)}
              className="btn-cyber text-xs flex items-center gap-1.5 py-2 px-4 bg-purple-400/20 border-purple-400 text-purple-300"
            >
              <Award size={14} /> Launch Assessment Runner
            </button>
          </div>

          {/* Pre vs Post Comparison Card */}
          {assessmentComparison && assessmentComparison.has_both ? (
            <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-400/10 via-cyan-400/10 to-transparent border border-purple-400/30 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <span className="text-slate-400 text-xs block mb-1">Pre-Assessment Baseline</span>
                <span className="text-2xl font-mono font-bold text-white">
                  {Math.round(assessmentComparison.pre_score * 100)}%
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-xs block mb-1">Post-Assessment Score</span>
                <span className="text-2xl font-mono font-bold text-cyan-400">
                  {Math.round(assessmentComparison.post_score * 100)}%
                </span>
              </div>
              <div>
                <span className="text-purple-300 text-xs block mb-1">Hake's Normalized Gain (g)</span>
                <span className="text-2xl font-mono font-bold text-purple-400">
                  {assessmentComparison.hake_normalized_gain !== null ? `${Math.round(assessmentComparison.hake_normalized_gain * 100)}%` : '—'}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Gross Gain: +{Math.round((assessmentComparison.gross_gain || 0) * 100)}%
                </span>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 flex items-center justify-between">
              <span>Complete both a Pre-Assessment and a Post-Assessment to compute Hake's normalized learning gain.</span>
              <button
                onClick={() => setIsAssessmentOpen(true)}
                className="btn-cyber text-xs py-1 px-3 ml-2"
              >
                Start Assessment
              </button>
            </div>
          )}

          {/* Past Assessment History Table */}
          <div className="space-y-3">
            <h4 className="font-display font-semibold text-white text-sm">Past Assessment Sessions</h4>
            {assessmentHistory.length === 0 ? (
              <div className="p-6 rounded-xl bg-white/4 border border-white/8 text-center text-slate-400 text-xs">
                No assessment sessions recorded yet for learner <span className="font-mono text-cyan-400">{learnerId}</span>.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="cyber-table">
                  <thead>
                    <tr>
                      <th className="text-left">Type</th>
                      <th className="text-left">Completed Date</th>
                      <th className="text-right">Score</th>
                      <th className="text-right">Correct / Total</th>
                      <th className="text-left">Assessment ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assessmentHistory.map(a => (
                      <tr key={a.assessment_id}>
                        <td>
                          <span className={`badge-chip text-[10px] uppercase font-bold ${
                            a.assessment_type === 'pre' ? 'text-cyan-400 bg-cyan-400/10' : 'text-purple-400 bg-purple-400/10'
                          }`}>
                            {a.assessment_type}
                          </span>
                        </td>
                        <td className="text-slate-300 text-xs">{a.completed_at ? new Date(a.completed_at).toLocaleString() : 'In Progress'}</td>
                        <td className="text-right font-mono font-bold text-white">
                          {a.score_pct != null ? `${a.score_pct}%` : (a.accuracy != null ? `${Math.round(a.accuracy * 100)}%` : (a.score != null ? `${Math.round((a.score / (a.total_questions || 1)) * 100)}%` : '—'))}
                        </td>
                        <td className="text-right font-mono text-slate-400 text-xs">{a.score ?? a.correct_count ?? 0} / {a.total_questions || 10}</td>
                        <td className="font-mono text-[10px] text-slate-500">{a.assessment_id?.slice(0, 12)}...</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── RESEARCH LAB TAB (Phase H) ── */}
      {activeTab === 'research lab' && (
        <ResearchLabSection />
      )}

      {/* ── MODEL TAB ── */}
      {activeTab === 'model' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex items-center gap-2 mb-2">
            <Info size={16} className="text-cyan-400" />
            <div className="font-display font-semibold text-white text-sm">Classification Benchmark & AutoML</div>
          </div>
          <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-sm text-slate-300 leading-relaxed">
            The platform classified your current level as <span className="text-cyan-400 font-semibold">{overallLevel}</span> based on:
            quiz score of <span className="font-mono text-white">{avgScore}%</span>, topic count of{' '}
            <span className="font-mono text-white">{assessment.length}</span>, and performance distribution.
            The <span className="text-purple-400">{modelName}</span> algorithm was selected by AutoML.
          </div>

          <div className="space-y-3">
            {Object.entries(modelScores).map(([name, score], i) => {
              const pct = parseFloat(String(score).replace('%', ''));
              const isTop = i === 0;
              return (
                <div key={name} className={`flex items-center gap-4 p-3 rounded-xl border transition-all ${
                  isTop ? 'bg-cyan-400/8 border-cyan-400/25' : 'bg-white/4 border-white/8'
                }`}>
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-mono font-bold ${
                    isTop ? 'bg-cyan-400 text-dark-300' : 'bg-white/10 text-slate-400'
                  }`}>
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <div className={`text-sm font-display font-semibold ${isTop ? 'text-cyan-400' : 'text-white'}`}>{name}</div>
                    <div className="difficulty-track mt-1 w-full">
                      <div className="difficulty-fill" style={{
                        width: `${pct}%`,
                        background: isTop ? 'linear-gradient(90deg, #00d4ff, #a855f7)' : 'rgba(148,163,184,0.4)'
                      }} />
                    </div>
                  </div>
                  <div className={`font-mono font-bold text-sm ${isTop ? 'text-cyan-400' : 'text-slate-400'}`}>{score}</div>
                  {isTop && <Star size={14} className="text-yellow-400" />}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Modals */}
      {selectedKCForModal && (
        <KCDetailModal
          kc={selectedKCForModal}
          onClose={() => setSelectedKCForModal(null)}
          onPractice={(topic) => {
            fetchRecommendation(undefined, topic);
            setActiveTab('overview');
          }}
        />
      )}

      {isAssessmentOpen && (
        <AssessmentModal
          isOpen={isAssessmentOpen}
          onClose={() => setIsAssessmentOpen(false)}
          onComplete={() => {
            fetchAssessments();
            fetchBktMastery();
          }}
        />
      )}

    </div>
  );
}
