import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Map, Play, Lock, CheckCircle, ChevronRight, ExternalLink,
  BookOpen, Video, Layers, ArrowRight, RefreshCw, Zap,
  Briefcase, Cpu, Network, Check, Calendar, Target, Flag, Clock
} from 'lucide-react';
import { apiFetch } from '../utils/api';
import VideoPlayerModal from '../components/VideoPlayerModal';

const STATUS_CONFIG = {
  completed:    { icon: CheckCircle, color: '#4ade80', bg: 'rgba(74,222,128,0.12)', border: 'rgba(74,222,128,0.35)', label: 'Mastered' },
  'in-progress':{ icon: Play,        color: '#fbbf24', bg: 'rgba(251,191,36,0.12)', border: 'rgba(251,191,36,0.35)',  label: 'In Progress' },
  recommended:  { icon: ChevronRight,color: '#00d4ff', bg: 'rgba(0,212,255,0.12)',  border: 'rgba(0,212,255,0.5)',   label: 'Ready' },
  ready:        { icon: ChevronRight,color: '#00d4ff', bg: 'rgba(0,212,255,0.12)',  border: 'rgba(0,212,255,0.5)',   label: 'Ready' },
  locked:       { icon: Lock,        color: '#475569', bg: 'rgba(71,85,105,0.12)',  border: 'rgba(71,85,105,0.3)',   label: 'Locked' },
};

const CAREER_TRACKS = [
  {
    id: 'placement',
    icon: Briefcase,
    title: 'ML for Placement',
    subtitle: 'Industry & Interview Ready',
    desc: 'Master the ML algorithms and foundations most frequently evaluated in technical interviews.',
    topics: ['Python', 'Statistics', 'Linear Regression', 'Classification', 'Decision Trees', 'Ensemble Methods', 'Neural Networks'],
    duration: '12 weeks',
    targetHours: 60,
    color: 'cyan',
  },
  {
    id: 'project',
    icon: Cpu,
    title: 'AI Product Engineering',
    subtitle: 'End-to-End Applications',
    desc: 'Build and deploy scalable machine learning services, automated pipelines, and cloud APIs.',
    topics: ['Python', 'Data Preprocessing', 'Linear Regression', 'Classification', 'Clustering', 'AutoML', 'Model Deployment'],
    duration: '10 weeks',
    targetHours: 50,
    color: 'purple',
  },
  {
    id: 'deeplearning',
    icon: Network,
    title: 'Deep Learning & NLP',
    subtitle: 'Modern Architectures & LLMs',
    desc: 'Comprehensive progression through feedforward networks, transformers, attention mechanisms, and RAG.',
    topics: ['Python', 'Probability', 'Neural Networks', 'NLP', 'Transformers', 'RAG', 'LLM'],
    duration: '16 weeks',
    targetHours: 80,
    color: 'emerald',
  },
];

function layoutNodes(steps) {
  const cols = Math.min(Math.max(Math.ceil(steps.length / 4), 3), 6);
  return steps.map((step, i) => ({
    ...step,
    x: (i % cols) * 190 + 50,
    y: Math.floor(i / cols) * 110 + 50,
  }));
}

function SVGGraph({ nodes, onSelect, selected }) {
  const svgW = Math.max(...nodes.map(n => n.x), 500) + 200;
  const svgH = Math.max(...nodes.map(n => n.y), 300) + 90;

  const edges = [];
  nodes.forEach(node => {
    node.prerequisites?.forEach(prereq => {
      const from = nodes.find(n => n.topic === prereq);
      if (from) {
        edges.push({ from, to: node });
      }
    });
  });

  return (
    <div className="overflow-x-auto p-4 rounded-2xl bg-slate-950/80 border border-white/10">
      <svg width={svgW} height={svgH} style={{ minWidth: 600 }}>
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.25)" />
          </marker>
        </defs>

        {/* Directed Prerequisite Edges */}
        {edges.map((e, i) => {
          const x1 = e.from.x + 80, y1 = e.from.y + 22;
          const x2 = e.to.x, y2 = e.to.y + 22;
          const mx = (x1 + x2) / 2;
          return (
            <path
              key={i}
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
              stroke={e.to.status === 'completed' ? 'rgba(74,222,128,0.4)' : 'rgba(0,212,255,0.2)'}
              strokeWidth="1.5"
              fill="none"
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Nodes */}
        {nodes.map(n => {
          const cfg = STATUS_CONFIG[n.status] || STATUS_CONFIG.ready;
          const isSel = selected?.topic === n.topic;
          return (
            <g
              key={n.topic}
              transform={`translate(${n.x},${n.y})`}
              onClick={() => onSelect(n)}
              style={{ cursor: 'pointer' }}
            >
              <rect
                width="160"
                height="44"
                rx="8"
                fill={isSel ? 'rgba(0,212,255,0.2)' : cfg.bg}
                stroke={isSel ? '#00d4ff' : cfg.border}
                strokeWidth={isSel ? 2 : 1}
              />
              <text x="14" y="27" fill={cfg.color} fontSize="12" fontWeight="600" fontFamily="DM Sans, sans-serif">
                {n.title || n.topic}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function LearningPlanPage() {
  // Views: 'curriculum_graph' | 'roadmap' | 'milestones'
  const [activeView, setActiveView] = useState('curriculum_graph');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [activeTrack, setActiveTrack] = useState('placement');
  const [videoModal, setVideoModal] = useState(null);

  const [pathData, setPathData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/learning-path')
      .then(data => {
        setPathData(data);
        if (data?.steps?.length > 0) {
          setSelectedTopic(data.steps[0]);
        }
        setLoading(false);
      })
      .catch(() => {
        // Fallback default path
        const fallbackSteps = [
          { topic: 'python', title: 'Python Foundations', status: 'completed', prerequisites: [], level: 'beginner', estimated_hours: 6 },
          { topic: 'statistics', title: 'Statistics & Math', status: 'completed', prerequisites: ['python'], level: 'beginner', estimated_hours: 8 },
          { topic: 'data preprocessing', title: 'Data Preprocessing', status: 'in-progress', prerequisites: ['python'], level: 'beginner', estimated_hours: 7 },
          { topic: 'linear regression', title: 'Linear Regression', status: 'ready', prerequisites: ['statistics', 'data preprocessing'], level: 'intermediate', estimated_hours: 10 },
          { topic: 'classification', title: 'Classification', status: 'ready', prerequisites: ['linear regression'], level: 'intermediate', estimated_hours: 10 },
          { topic: 'neural networks', title: 'Neural Networks', status: 'locked', prerequisites: ['classification'], level: 'advanced', estimated_hours: 14 },
          { topic: 'nlp', title: 'Natural Language Proc.', status: 'locked', prerequisites: ['neural networks'], level: 'advanced', estimated_hours: 12 },
        ];
        setPathData({ steps: fallbackSteps, overall_progress_pct: 35 });
        setSelectedTopic(fallbackSteps[2]);
        setLoading(false);
      });
  }, []);

  const steps = pathData?.steps || [];
  const nodes = layoutNodes(steps);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
              CURRICULUM ARCHITECTURE
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-400/10 text-purple-400 border border-purple-400/20">
              TOPOLOGICAL PREREQUISITE DAG
            </span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">My Learning Plan</h1>
          <p className="text-slate-400 text-sm mt-1">
            Structured roadmap ensuring concepts are mastered in strictly valid prerequisite sequence without hidden knowledge gaps.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-white/5 rounded-xl border border-white/10 text-xs">
          <button
            onClick={() => setActiveView('curriculum_graph')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeView === 'curriculum_graph' ? 'bg-cyan-400 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Map size={13} />
            <span>Curriculum DAG</span>
          </button>
          <button
            onClick={() => setActiveView('roadmap')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeView === 'roadmap' ? 'bg-cyan-400 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers size={13} />
            <span>Sequential Roadmap</span>
          </button>
          <button
            onClick={() => setActiveView('milestones')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeView === 'milestones' ? 'bg-cyan-400 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Target size={13} />
            <span>Career Milestones</span>
          </button>
        </div>
      </div>

      {/* VIEW 1: Interactive Curriculum Graph */}
      {activeView === 'curriculum_graph' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <SVGGraph nodes={nodes} onSelect={setSelectedTopic} selected={selectedTopic} />
              <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-1 px-2">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Mastered</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400" /> In Progress</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Prerequisite Ready</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-600" /> Locked Gap</span>
                </div>
                <span>Click node for topic syllabus</span>
              </div>
            </div>

            {/* Selected Topic Inspector */}
            <div className="glass-card p-6 space-y-4 lg:col-span-1 flex flex-col justify-between">
              {selectedTopic ? (
                <div className="space-y-4">
                  <div className="border-b border-white/10 pb-3">
                    <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block">INSPECTED CONCEPT</span>
                    <h3 className="font-display font-bold text-white text-lg">{selectedTopic.title || selectedTopic.topic}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-white/10 text-slate-300">
                        Level: {selectedTopic.level || 'Intermediate'}
                      </span>
                      <span className="text-slate-400 text-xs">~{selectedTopic.estimated_hours || 8} hrs</span>
                    </div>
                  </div>

                  <div className="space-y-2 text-xs">
                    <span className="font-mono text-slate-400 block">TOPOLOGICAL PREREQUISITES</span>
                    {selectedTopic.prerequisites?.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedTopic.prerequisites.map((p, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300 font-mono text-[11px]">
                            {p}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-emerald-400 text-[11px]">Foundational Entry Concept (No upstream dependencies).</span>
                    )}
                  </div>

                  <div className="pt-2">
                    <Link
                      to={`/learn?mode=continue&topic=${encodeURIComponent(selectedTopic.topic)}`}
                      className="btn-cyber-solid text-xs w-full py-2.5 flex items-center justify-center gap-2"
                    >
                      <Play size={13} />
                      <span>Learn This Concept</span>
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-xs text-center py-8">Select a node from the curriculum graph.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: Sequential Roadmap */}
      {activeView === 'roadmap' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <h3 className="font-display font-bold text-white text-lg">Topological Sequence</h3>
              <p className="text-slate-400 text-xs mt-0.5">Recommended linear progression derived from graph topological sorting.</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-400/10 px-2.5 py-1 rounded-lg">
              {steps.filter(s => s.status === 'completed').length} / {steps.length} Steps Mastered
            </span>
          </div>

          <div className="space-y-3">
            {steps.map((st, i) => {
              const cfg = STATUS_CONFIG[st.status] || STATUS_CONFIG.ready;
              const Icon = cfg.icon;
              return (
                <div
                  key={i}
                  className="p-4 rounded-xl border flex items-center justify-between transition-all"
                  style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: cfg.color }}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <div className="font-bold text-white text-sm">{st.title || st.topic}</div>
                      <div className="text-[11px] text-slate-400">
                        Stage {i + 1} · {st.estimated_hours || 8} study hours · Prerequisites: {st.prerequisites?.length ? st.prerequisites.join(', ') : 'None'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono font-bold" style={{ color: cfg.color }}>
                      {cfg.label}
                    </span>
                    <Link
                      to={`/learn?mode=continue&topic=${encodeURIComponent(st.topic)}`}
                      className="btn-cyber text-xs py-1.5 px-3"
                    >
                      Open
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 3: Career Milestones & Goal Tracks */}
      {activeView === 'milestones' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {CAREER_TRACKS.map(trk => {
              const isSelected = activeTrack === trk.id;
              const Icon = trk.icon;
              return (
                <div
                  key={trk.id}
                  onClick={() => setActiveTrack(trk.id)}
                  className={`glass-card p-6 flex flex-col justify-between cursor-pointer transition-all border ${
                    isSelected ? 'border-cyan-400 shadow-lg shadow-cyan-400/10' : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center text-cyan-400">
                        <Icon size={20} />
                      </div>
                      {isSelected && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-400/20 text-cyan-300">
                          Active Track
                        </span>
                      )}
                    </div>
                    <div>
                      <h4 className="font-display font-bold text-white text-base">{trk.title}</h4>
                      <p className="text-slate-400 text-xs mt-1 leading-relaxed">{trk.desc}</p>
                    </div>

                    <div className="space-y-1.5 pt-2 text-xs">
                      <span className="font-mono text-slate-500 text-[10px] uppercase">Curriculum Milestones:</span>
                      <div className="flex flex-wrap gap-1">
                        {trk.topics.map((t, idx) => (
                          <span key={idx} className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/5 text-slate-300">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/5 mt-4 flex items-center justify-between text-xs text-slate-400">
                    <span>{trk.duration}</span>
                    <span className="font-mono text-cyan-400">~{trk.targetHours} Hours</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
