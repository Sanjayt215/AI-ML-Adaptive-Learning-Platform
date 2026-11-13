import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Map, Play, Lock, CheckCircle, ChevronRight, ExternalLink, BookOpen, Video, Layers, ArrowRight, RefreshCw, Zap } from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import { apiFetch } from '../utils/api';
import VideoPlayerModal from '../components/VideoPlayerModal';

const STATUS_CONFIG = {
  completed:    { icon: CheckCircle, color: '#4ade80', bg: 'rgba(74,222,128,0.12)', border: 'rgba(74,222,128,0.35)', label: 'Mastered' },
  'in-progress':{ icon: Play,        color: '#fbbf24', bg: 'rgba(251,191,36,0.12)', border: 'rgba(251,191,36,0.35)',  label: 'In Progress' },
  recommended:  { icon: ChevronRight,color: '#00d4ff', bg: 'rgba(0,212,255,0.12)',  border: 'rgba(0,212,255,0.5)',   label: 'Ready' },
  ready:        { icon: ChevronRight,color: '#00d4ff', bg: 'rgba(0,212,255,0.12)',  border: 'rgba(0,212,255,0.5)',   label: 'Ready' },
  locked:       { icon: Lock,        color: '#475569', bg: 'rgba(71,85,105,0.12)',  border: 'rgba(71,85,105,0.3)',   label: 'Locked' },
};

const LEVEL_COLOR = { beginner: '#4ade80', intermediate: '#fbbf24', advanced: '#f87171' };

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
    <div className="overflow-x-auto">
      <svg width={svgW} height={svgH} style={{ minWidth: 600 }}>
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.25)" />
          </marker>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((e, i) => {
          const x1 = e.from.x + 80, y1 = e.from.y + 22;
          const x2 = e.to.x, y2 = e.to.y + 22;
          const mx = (x1 + x2) / 2;
          return (
            <path
              key={i}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              fill="none"
              stroke="rgba(255,255,255,0.12)"
              strokeWidth={1.5}
              strokeDasharray={e.to.status === 'locked' ? '4,4' : '0'}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const cfg = STATUS_CONFIG[node.status] || STATUS_CONFIG.locked;
          const isSelected = selected?.topic === node.topic;
          return (
            <g key={node.topic} transform={`translate(${node.x}, ${node.y})`}
              onClick={() => onSelect(node)}
              style={{ cursor: 'pointer' }}>
              <rect
                x={0} y={0} width={160} height={46} rx={12}
                fill={isSelected ? cfg.bg : 'rgba(255,255,255,0.05)'}
                stroke={isSelected ? cfg.color : cfg.border}
                strokeWidth={isSelected ? 2 : 1}
                filter={isSelected ? 'url(#nodeGlow)' : undefined}
              />
              <circle cx={15} cy={23} r={5} fill={cfg.color} opacity={0.9} />
              <text x={28} y={19} fill={cfg.color} fontSize={10} fontFamily="Space Grotesk" fontWeight="600" textAnchor="start">
                {node.topic.toUpperCase().slice(0, 15)}
              </text>
              <text x={28} y={32} fill="rgba(148,163,184,0.8)" fontSize={9} fontFamily="JetBrains Mono">
                {cfg.label} · {node.level || 'level 1'}
              </text>
              <rect x={126} y={7} width={26} height={15} rx={4} fill="rgba(255,255,255,0.08)" />
              <text x={139} y={18} fill="#94a3b8" fontSize={9} fontFamily="JetBrains Mono" fontWeight="600" textAnchor="middle">
                #{node.order}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function LearningPathPage() {
  const { learningPath: flaskPath, profile, learningScore, refresh } = useFlaskData();
  const [curriculumPlan, setCurriculumPlan] = useState(null);
  const [curriculumLoading, setCurriculumLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [saving, setSaving] = useState(false);
  const [topicResources, setTopicResources] = useState(null);
  const [videoModal, setVideoModal] = useState({ open: false, video: null });
  const [errorMessage, setErrorMessage] = useState('');

  const learnerId = localStorage.getItem('autolearn_learner_id') || 'learner_default';

  const fetchCurriculum = async () => {
    setCurriculumLoading(true);
    try {
      const data = await apiFetch(`/api/curriculum/plan?learner_id=${learnerId}`);
      if (data && data.ok) {
        setCurriculumPlan(data);
      }
    } catch (err) {
      console.warn('Curriculum plan fetch error:', err);
    } finally {
      setCurriculumLoading(false);
    }
  };

  useEffect(() => {
    fetchCurriculum();
  }, []);

  // Merge flaskPath with full curriculum plan if available
  const activePath = React.useMemo(() => {
    if (flaskPath && flaskPath.length > 0) {
      return flaskPath;
    }
    if (curriculumPlan && curriculumPlan.stages) {
      const flat = [];
      let order = 1;
      curriculumPlan.stages.forEach(stage => {
        stage.topics?.forEach(t => {
          flat.push({
            topic: t.topic,
            level: stage.stage_number === 1 ? 'beginner' : stage.stage_number === 2 ? 'intermediate' : 'advanced',
            status: t.status === 'mastered' ? 'completed' : t.status === 'ready' ? 'recommended' : t.status === 'in_progress' ? 'in-progress' : 'locked',
            order: order++,
            project: `Complete targeted exercises for ${t.topic.replace(/_/g, ' ')}.`,
            prerequisites: t.prerequisites || [],
            current_mastery: t.current_mastery,
          });
        });
      });
      return flat;
    }
    return [];
  }, [flaskPath, curriculumPlan]);

  const nodes = layoutNodes(activePath);

  useEffect(() => {
    if (!selected && activePath.length > 0) {
      const rec = activePath.find(s => s.status === 'recommended') || activePath[0];
      setSelected(rec);
    }
  }, [activePath, selected]);

  const updateStatus = async (topic, status) => {
    setSaving(true);
    setErrorMessage('');
    try {
      await apiFetch('/api/path/step/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, status }),
      });
      await refresh();
      await fetchCurriculum();
    } catch (err) {
      console.error('Path status update failed:', err);
      setErrorMessage(err.message || 'Unable to update the step right now.');
    } finally {
      setSaving(false);
    }
  };

  const fetchTopicResources = async (topic) => {
    if (!topic) {
      setTopicResources(null);
      return;
    }
    try {
      const data = await apiFetch(`/api/path/resources?topic=${encodeURIComponent(topic)}`);
      setTopicResources(data.resources || null);
    } catch {
      setTopicResources(null);
    }
  };

  const handleOpenVideo = async (video) => {
    setErrorMessage('');
    setVideoModal({ open: true, video });
    if (!video) return;
    try {
      await apiFetch('/api/path/video/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: selected.topic, url: video.url, event: 'start' }),
      });
      await refresh();
    } catch (err) {
      console.error('Video start tracking failed:', err);
    }
  };

  const handleTrackVideo = async ({ watched_seconds, watched_pct, event }) => {
    if (!selected || !videoModal.video) return;
    try {
      await apiFetch('/api/path/video/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: selected.topic,
          url: videoModal.video.url,
          watched_seconds,
          watched_pct,
          event,
        }),
      });
      await refresh();
    } catch (err) {
      console.error('Video progress tracking failed:', err);
    }
  };

  useEffect(() => {
    if (selected) {
      fetchTopicResources(selected.topic);
    }
  }, [selected]);

  const displayedResources = topicResources || selected;
  const completedCount = activePath.filter(s => s.status === 'completed').length;
  const completionPct = activePath.length ? Math.round((completedCount / activePath.length) * 100) : 0;

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Map size={20} className="text-cyan-400" />
            <h1 className="font-display font-bold text-2xl text-white">Prerequisite DAG & Curriculum Path</h1>
          </div>
          <p className="text-slate-400 text-xs">
            Topologically sorted knowledge graph · Prerequisites enforce mastery threshold &ge; 60%
          </p>
        </div>
        <div className="flex gap-3 flex-wrap text-xs">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <div key={key} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: cfg.color }} />
              <span className="text-slate-400">{cfg.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Grid: Graph + Detail */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Graph */}
        <div className="xl:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="font-display font-semibold text-white text-sm">Interactive Prerequisite Graph</div>
            <button
              onClick={fetchCurriculum}
              disabled={curriculumLoading}
              className="btn-cyber text-xs py-1 px-2.5 flex items-center gap-1"
            >
              <RefreshCw size={11} className={curriculumLoading ? 'animate-spin' : ''} />
              Refresh Graph
            </button>
          </div>

          <SVGGraph nodes={nodes} onSelect={setSelected} selected={selected} />

          {/* Progress bar */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400">Curriculum Mastery Progress</span>
              <span className="text-cyan-400 font-mono">
                {completedCount} / {activePath.length} Mastered ({completionPct}%)
              </span>
            </div>
            <div className="difficulty-track">
              <div
                className="difficulty-fill bg-gradient-to-r from-cyan-400 to-purple-500"
                style={{ width: `${completionPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Detail panel */}
        <div className="glass-card p-6">
          {selected ? (
            <div className="space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-2.5 h-2.5 rounded-full animate-pulse"
                    style={{ background: STATUS_CONFIG[selected.status]?.color }}
                  />
                  <span className="font-display font-bold text-white text-lg capitalize">
                    {selected.topic.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="badge-chip capitalize"
                    style={{
                      color: LEVEL_COLOR[selected.level] || '#00d4ff',
                      background: `${LEVEL_COLOR[selected.level] || '#00d4ff'}18`,
                      border: `1px solid ${LEVEL_COLOR[selected.level] || '#00d4ff'}33`,
                    }}
                  >
                    {selected.level || 'Beginner'}
                  </span>
                  <span className="text-xs text-slate-500">Step #{selected.order}</span>
                </div>
              </div>

              {/* Status explanation */}
              {selected.status === 'locked' && (
                <div className="p-3 rounded-xl bg-red-400/10 border border-red-400/20 text-xs text-red-300">
                  <div className="font-semibold mb-0.5">Prerequisite Lock Active</div>
                  <span>Prerequisite concepts must achieve &ge; 60% mastery before this topic can be unlocked for adaptive practice.</span>
                </div>
              )}

              {/* Practice button */}
              <div className="space-y-2">
                <Link
                  to="/dashboard"
                  className="btn-cyber text-xs w-full py-2.5 flex items-center justify-center gap-1.5"
                >
                  <Zap size={14} /> Practice in Adaptive Dashboard
                </Link>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    disabled={saving}
                    onClick={() => updateStatus(selected.topic, 'in-progress')}
                    className="btn-cyber text-xs py-1.5"
                  >
                    Mark In-Progress
                  </button>
                  <button
                    disabled={saving}
                    onClick={() => updateStatus(selected.topic, 'completed')}
                    className="btn-cyber text-xs py-1.5 text-green-400 border-green-400/30"
                  >
                    Mark Mastered
                  </button>
                </div>
              </div>

              {errorMessage && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                  {errorMessage}
                </div>
              )}

              {/* Mini Project */}
              <div className="p-3 rounded-xl bg-purple-400/5 border border-purple-400/20">
                <div className="text-xs text-purple-400 font-semibold mb-1">🎯 Practice Objective</div>
                <div className="text-slate-300 text-xs leading-relaxed">{selected.project}</div>
              </div>

              {/* Prerequisites list */}
              {selected.prerequisites?.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Prerequisites Required:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.prerequisites.map(p => (
                      <span
                        key={p}
                        className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-xs font-mono capitalize"
                      >
                        {p.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Videos */}
              {displayedResources?.videos?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Video size={13} className="text-red-400" />
                    <span className="text-xs text-slate-400 font-semibold">Recommended Videos</span>
                  </div>
                  <div className="space-y-2">
                    {displayedResources.videos.map((v, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleOpenVideo(v)}
                        className="w-full text-left flex items-start gap-2 p-2.5 rounded-xl bg-white/4 border border-white/8 hover:border-white/15 transition-all group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-red-400/10 flex items-center justify-center flex-shrink-0">
                          <Play size={11} className="text-red-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-white text-xs font-medium leading-tight truncate group-hover:text-cyan-400 transition-colors">
                            {v.title}
                          </div>
                          <div className="text-slate-500 text-[10px] mt-0.5">{v.channel}</div>
                        </div>
                        <ExternalLink size={11} className="text-slate-600 group-hover:text-cyan-400 flex-shrink-0 mt-0.5 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <VideoPlayerModal
                open={videoModal.open}
                video={videoModal.video}
                onClose={() => setVideoModal({ open: false, video: null })}
                onWatchUpdate={handleTrackVideo}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <Map size={32} className="text-slate-600 mb-3" />
              <div className="text-slate-500 text-sm">Select any topic node</div>
              <div className="text-slate-600 text-xs mt-1">to inspect prerequisites and start practice</div>
            </div>
          )}
        </div>
      </div>

      {/* 4 Progression Stages Breakdown */}
      {curriculumPlan && curriculumPlan.stages && (
        <div className="glass-card p-6 space-y-4">
          <div className="font-display font-semibold text-white text-sm">Curriculum Progression Stages</div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {curriculumPlan.stages.map(stage => (
              <div key={stage.stage_number} className="p-4 rounded-xl bg-white/4 border border-white/8 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold text-white text-sm">{stage.stage_title}</span>
                  <span className="badge-chip border border-white/10 text-slate-400 text-xs">
                    {stage.topics?.length || 0} KCs
                  </span>
                </div>
                <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                  {stage.topics?.map(t => (
                    <div
                      key={t.topic}
                      onClick={() => {
                        const match = activePath.find(p => p.topic === t.topic);
                        if (match) setSelected(match);
                      }}
                      className="flex items-center justify-between text-xs py-1.5 px-2 rounded-lg hover:bg-white/5 cursor-pointer border-b border-white/5 transition"
                    >
                      <span className="capitalize text-slate-300 font-medium truncate max-w-[120px]">
                        {t.topic.replace(/_/g, ' ')}
                      </span>
                      <span className={`badge-chip text-[9px] ${
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
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
