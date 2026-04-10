import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, Cell,
} from 'recharts';
import {
  LayoutDashboard, TrendingUp, Brain, BookOpen, Zap, Target,
  ArrowRight, Info, ChevronRight, Cpu, Database, Star
} from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import StatCard from '../components/StatCard';
import HeatmapGrid from '../components/HeatmapGrid';
import ProgressRing from '../components/ProgressRing';

const LEVEL_CONFIG = {
  advanced:     { label: 'Advanced',     color: '#f87171', bg: 'bg-red-400/10',    border: 'border-red-400/30',    ring: '#f87171' },
  intermediate: { label: 'Intermediate', color: '#fbbf24', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', ring: '#fbbf24' },
  beginner:     { label: 'Beginner',     color: '#4ade80', bg: 'bg-green-400/10',  border: 'border-green-400/30',  ring: '#4ade80' },
};

function CustomTooltip({ active, payload, label, aiFeatures = [], mlFeatures = [], datasetRegistry = [], llmMode = '', datasetSources = [] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip-cyber">
      <div className="font-display font-semibold text-white mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="text-xs flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.name}:</span>
          <span className="text-white font-mono font-medium">{p.value}%</span>
        </div>
      ))}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="glass-card p-5 lg:col-span-2">
          <div className="font-display font-semibold text-white text-sm mb-3">AI + ML capabilities</div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <div className="text-cyan-400 text-xs mb-2">AI features</div>
              <div className="space-y-2">{(aiFeatures || []).map((f, i) => <div key={i} className="text-sm text-slate-300">• {f}</div>)}</div>
            </div>
            <div>
              <div className="text-purple-400 text-xs mb-2">ML features</div>
              <div className="space-y-2">{(mlFeatures || []).map((f, i) => <div key={i} className="text-sm text-slate-300">• {f}</div>)}</div>
            </div>
          </div>
        </div>
        <div className="glass-card p-5">
          <div className="font-display font-semibold text-white text-sm mb-3">Data + tutor status</div>
          <div className="text-sm text-slate-300 mb-2">Tutor mode: <span className="text-cyan-400">{llmMode}</span></div>
          <div className="text-sm text-slate-300 mb-2">Dataset sources:</div>
          <div className="flex flex-wrap gap-2 mb-3">{(datasetSources || []).map((s, i) => <span key={i} className="badge-chip">{s}</span>)}</div>
          <div className="text-xs text-slate-500">Registry items: {datasetRegistry?.length || 0}</div>
        </div>
      </div>

    </div>
  );
}

export default function DashboardPage() {
  const {
    assessment, profile, modelScores, dataInfo,
    modelName, automlEngine, avgScore,
    strengths, weakTopics, accuracyTrend, topicMastery, modernFeatures, learningScore, aiFeatures, mlFeatures, datasetRegistry, llmMode, datasetSources,
  } = useFlaskData();

  const [activeTab, setActiveTab] = useState('overview');

  const overallLevel = avgScore >= 75 ? 'advanced' : avgScore >= 45 ? 'intermediate' : 'beginner';
  const lvlCfg = LEVEL_CONFIG[overallLevel];

  const radarData = topicMastery.map(t => ({ subject: t.topic, A: t.mastery, fullMark: 100 }));

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">

      {/* Top bar */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="font-display font-bold text-2xl text-white">Student Dashboard</h1>
            <span className={`badge-chip border ${lvlCfg.bg} ${lvlCfg.border}`}
              style={{ color: lvlCfg.color }}>
              {lvlCfg.label}
            </span>
          </div>
          <p className="text-slate-500 text-sm">
            Goal: <span className="text-slate-300">{profile?.target_goal || 'ML for placement'}</span>
          </p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <Link to="/resources" className="btn-cyber text-sm">Open Resources <ArrowRight size={14} /></Link>
          <Link to="/path" className="btn-cyber text-sm">Learning Path <ArrowRight size={14} /></Link>
          <Link to="/start" className="btn-cyber text-sm text-red-400 border-red-400/30 hover:border-red-400/60">New Plan</Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={TrendingUp}     label="Avg Quiz Score"   value={`${avgScore}%`}         color="cyan"   trend={+12} />
        <StatCard icon={Zap}            label="Learning Score"  value={`${learningScore || 0}%`}   color="green" />
        <StatCard icon={BookOpen}       label="Topics Chosen"    value={profile?.topics?.length || 0} color="purple" />
        <StatCard icon={Cpu}            label="Best Classifier"  value={modelName}               color="green"  sub={automlEngine} />
        <StatCard icon={Database}       label="Training Rows"    value={dataInfo?.rows || '—'}   color="pink"   sub={dataInfo?.real_data_used ? 'Real Kaggle' : 'Sample data'} />
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 p-1 glass-card w-fit">
        {['overview', 'analytics', 'topics', 'model'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-xl text-sm font-display font-medium transition-all capitalize
              ${activeTab === tab
                ? 'bg-cyan-400/15 text-cyan-400 border border-cyan-400/30'
                : 'text-slate-400 hover:text-slate-200'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Level ring + summary */}
          <div className="glass-card p-6 flex flex-col items-center gap-4">
            <div className="font-display font-semibold text-white text-sm w-full">Overall Level</div>
            <ProgressRing
              value={avgScore}
              size={130}
              stroke={10}
              color={lvlCfg.ring}
              label={lvlCfg.label}
              sublabel={`${avgScore}% avg score`}
            />
            <div className="w-full space-y-2">
              {assessment.map(item => {
                const cfg = LEVEL_CONFIG[item.predicted_level] || LEVEL_CONFIG.beginner;
                return (
                  <div key={item.topic} className="flex items-center gap-2">
                    <div className="flex-1 text-xs text-slate-400 capitalize">{item.topic}</div>
                    <div className="w-24 difficulty-track">
                      <div className="difficulty-fill" style={{ width: `${item.score_pct}%`, background: cfg.color }} />
                    </div>
                    <div className="w-8 text-right font-mono text-xs" style={{ color: cfg.color }}>{item.score_pct}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Assessment table */}
          <div className="lg:col-span-2 glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-4">Assessment Results by Topic</div>
            <div className="overflow-x-auto">
              <table className="cyber-table">
                <thead>
                  <tr>
                    <th className="text-left">Topic</th>
                    <th className="text-left">Quiz Score</th>
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

            {/* Focus areas */}
            <div className="mt-5 pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
              <div className="glass-card p-3">
                <div className="text-xs text-slate-500 mb-1">⚠ Weak Areas</div>
                <div className="font-display font-medium text-red-400 text-sm capitalize">
                  {weakTopics.length ? weakTopics.join(', ') : 'None — great job!'}
                </div>
              </div>
              <div className="glass-card p-3">
                <div className="text-xs text-slate-500 mb-1">✦ Strengths</div>
                <div className="font-display font-medium text-green-400 text-sm capitalize">
                  {strengths.length ? strengths.join(', ') : 'Keep practicing!'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── ANALYTICS TAB ── */}
      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Accuracy trend line chart */}
          <div className="glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-1">Accuracy Trend</div>
            <div className="text-slate-500 text-xs mb-5">Daily quiz accuracy vs target</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={accuracyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={
                  <CustomTooltip
                    aiFeatures={aiFeatures}
                    mlFeatures={mlFeatures}
                    datasetRegistry={datasetRegistry}
                    llmMode={llmMode}
                    datasetSources={datasetSources}
                  />
                } />
                <Line type="monotone" dataKey="accuracy" stroke="#00d4ff" strokeWidth={2.5} dot={{ fill: '#00d4ff', r: 4, strokeWidth: 0 }} name="Accuracy" activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="target" stroke="rgba(168,85,247,0.4)" strokeWidth={1.5} strokeDasharray="5 5" dot={false} name="Target" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Topic mastery bar */}
          <div className="glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-1">Topic Mastery</div>
            <div className="text-slate-500 text-xs mb-5">Quiz scores per topic</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={topicMastery} barSize={24}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="topic" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={
                  <CustomTooltip
                    aiFeatures={aiFeatures}
                    mlFeatures={mlFeatures}
                    datasetRegistry={datasetRegistry}
                    llmMode={llmMode}
                    datasetSources={datasetSources}
                  />
                } />
                <Bar dataKey="mastery" name="Mastery" radius={[6, 6, 0, 0]}>
                  {topicMastery.map((entry, i) => (
                    <Cell key={i} fill={entry.mastery >= 75 ? '#4ade80' : entry.mastery >= 50 ? '#fbbf24' : entry.mastery >= 30 ? '#fb923c' : '#f87171'} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar chart */}
          <div className="glass-card p-6 lg:col-span-2">
            <div className="font-display font-semibold text-white text-sm mb-1">Learning Radar</div>
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
          <div className="text-slate-500 text-xs mb-6">Hover a cell for details. Color = mastery level.</div>
          <HeatmapGrid assessment={assessment} />

          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="font-display font-semibold text-white text-sm mb-3">Priority Study Order</div>
              <div className="space-y-2">
                {[...assessment].sort((a, b) => a.score_pct - b.score_pct).map((item, i) => {
                  const cfg = LEVEL_CONFIG[item.predicted_level] || LEVEL_CONFIG.beginner;
                  return (
                    <div key={item.topic} className="flex items-center gap-3 p-3 rounded-xl bg-white/4 border border-white/8">
                      <div className="w-6 h-6 rounded-lg bg-white/10 flex items-center justify-center text-xs font-mono text-slate-400">{i + 1}</div>
                      <div className="flex-1">
                        <div className="text-white text-sm capitalize font-medium">{item.topic}</div>
                        <div className="text-xs" style={{ color: cfg.color }}>{item.predicted_level}</div>
                      </div>
                      <div className="font-mono text-sm font-bold" style={{ color: cfg.color }}>{item.score_pct}%</div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div>
              <div className="font-display font-semibold text-white text-sm mb-3">Recommended Next Steps</div>
              <div className="space-y-3">
                {weakTopics.slice(0, 4).map(topic => (
                  <div key={topic} className="p-3 rounded-xl bg-red-400/5 border border-red-400/20">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                      <span className="text-red-400 text-sm font-semibold capitalize">{topic}</span>
                    </div>
                    <div className="text-slate-500 text-xs">Focus area — go to Resources for curated videos and courses</div>
                  </div>
                ))}
                {weakTopics.length === 0 && (
                  <div className="p-4 rounded-xl bg-green-400/5 border border-green-400/20 text-green-400 text-sm">
                    ✦ No critical weak topics! Consider advancing to deeper resources.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── MODEL TAB ── */}
      {activeTab === 'model' && (
        <div className="space-y-6">
          {/* Model explanation */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Info size={16} className="text-cyan-400" />
              <div className="font-display font-semibold text-white text-sm">Why this prediction?</div>
            </div>
            <div className="p-4 rounded-xl bg-cyan-400/5 border border-cyan-400/20 text-sm text-slate-300 leading-relaxed mb-5">
              The model classified you as <span className="text-cyan-400 font-semibold">{overallLevel}</span> based on:
              your quiz score of <span className="font-mono text-white">{avgScore}%</span>, topic count of{' '}
              <span className="font-mono text-white">{assessment.length}</span>, and performance distribution across weak
              vs strong topics. The <span className="text-purple-400">{modelName}</span> algorithm was selected by AutoML
              as the best performing classifier on the training set.
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {modernFeatures.map(f => (
                <div key={f.name} className="p-3 rounded-xl bg-white/4 border border-white/8">
                  <div className="font-display font-semibold text-cyan-400 text-sm mb-1">{f.name}</div>
                  <div className="text-slate-400 text-xs leading-relaxed">{f.why}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Model leaderboard */}
          <div className="glass-card p-6">
            <div className="font-display font-semibold text-white text-sm mb-4">Classification Benchmark</div>
            <div className="space-y-3">
              {Object.entries(modelScores).map(([name, score], i) => {
                const pct = parseFloat(String(score).replace('%', ''));
                const isTop = i === 0;
                return (
                  <div key={name} className={`flex items-center gap-4 p-3 rounded-xl border transition-all
                    ${isTop ? 'bg-cyan-400/8 border-cyan-400/25' : 'bg-white/4 border-white/8'}`}>
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-mono font-bold
                      ${isTop ? 'bg-cyan-400 text-dark-300' : 'bg-white/10 text-slate-400'}`}>
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
        </div>
      )}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="glass-card p-5 lg:col-span-2">
          <div className="font-display font-semibold text-white text-sm mb-3">AI + ML capabilities</div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <div className="text-cyan-400 text-xs mb-2">AI features</div>
              <div className="space-y-2">{(aiFeatures || []).map((f, i) => <div key={i} className="text-sm text-slate-300">• {f}</div>)}</div>
            </div>
            <div>
              <div className="text-purple-400 text-xs mb-2">ML features</div>
              <div className="space-y-2">{(mlFeatures || []).map((f, i) => <div key={i} className="text-sm text-slate-300">• {f}</div>)}</div>
            </div>
          </div>
        </div>
        <div className="glass-card p-5">
          <div className="font-display font-semibold text-white text-sm mb-3">Data + tutor status</div>
          <div className="text-sm text-slate-300 mb-2">Tutor mode: <span className="text-cyan-400">{llmMode}</span></div>
          <div className="text-sm text-slate-300 mb-2">Dataset sources:</div>
          <div className="flex flex-wrap gap-2 mb-3">{(datasetSources || []).map((s, i) => <span key={i} className="badge-chip">{s}</span>)}</div>
          <div className="text-xs text-slate-500">Registry items: {datasetRegistry?.length || 0}</div>
        </div>
      </div>

    </div>
  );
}
