import React, { useState, useRef, useEffect } from 'react';
import { Map, Play, Lock, CheckCircle, ChevronRight, ExternalLink, BookOpen, Video, Layers } from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import { apiFetch } from '../utils/api';
import VideoPlayerModal from '../components/VideoPlayerModal';

const STATUS_CONFIG = {
  completed:    { icon: CheckCircle, color: '#4ade80', bg: 'rgba(74,222,128,0.12)', border: 'rgba(74,222,128,0.35)', label: 'Completed' },
  'in-progress':{ icon: Play,        color: '#fbbf24', bg: 'rgba(251,191,36,0.12)', border: 'rgba(251,191,36,0.35)',  label: 'In Progress' },
  recommended:  { icon: ChevronRight,color: '#00d4ff', bg: 'rgba(0,212,255,0.12)',  border: 'rgba(0,212,255,0.5)',  label: 'Not Started' },
  locked:       { icon: Lock,        color: '#475569', bg: 'rgba(71,85,105,0.12)',  border: 'rgba(71,85,105,0.3)',  label: 'Locked' },
};

const LEVEL_COLOR = { beginner: '#4ade80', intermediate: '#fbbf24', advanced: '#f87171' };

// Simple layered layout: place nodes in columns based on order
function layoutNodes(steps) {
  const cols = Math.ceil(steps.length / 3);
  return steps.map((step, i) => ({
    ...step,
    x: (i % cols) * 180 + 60,
    y: Math.floor(i / cols) * 110 + 50,
  }));
}

function SVGGraph({ nodes, onSelect, selected }) {
  const svgW = Math.max(...nodes.map(n => n.x)) + 180;
  const svgH = Math.max(...nodes.map(n => n.y)) + 80;

  // Draw edges based on prerequisites
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
      <svg width={svgW} height={svgH} style={{ minWidth: 500 }}>
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.2)" />
          </marker>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((e, i) => {
          const x1 = e.from.x + 70, y1 = e.from.y + 22;
          const x2 = e.to.x, y2 = e.to.y + 22;
          const mx = (x1 + x2) / 2;
          return (
            <path
              key={i}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth={1.5}
              strokeDasharray={e.to.status === 'locked' ? '5,4' : '0'}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const cfg = STATUS_CONFIG[node.status] || STATUS_CONFIG.locked;
          const isSelected = selected?.topic === node.topic;
          const StatusIcon = cfg.icon;
          return (
            <g key={node.topic} transform={`translate(${node.x}, ${node.y})`}
              onClick={() => node.status !== 'locked' && onSelect(node)}
              style={{ cursor: node.status !== 'locked' ? 'pointer' : 'not-allowed' }}>
              <rect
                x={0} y={0} width={150} height={44} rx={12}
                fill={isSelected ? cfg.bg : 'rgba(255,255,255,0.05)'}
                stroke={isSelected ? cfg.border : cfg.border}
                strokeWidth={isSelected ? 2 : 1}
                filter={isSelected ? 'url(#nodeGlow)' : undefined}
              />
              {/* Status dot */}
              <circle cx={14} cy={22} r={5} fill={cfg.color} opacity={0.9} />
              {/* Label */}
              <text x={26} y={18} fill={cfg.color} fontSize={10} fontFamily="Space Grotesk" fontWeight="600" textAnchor="start">
                {node.topic.toUpperCase().slice(0, 14)}
              </text>
              <text x={26} y={31} fill="rgba(148,163,184,0.8)" fontSize={9} fontFamily="JetBrains Mono">
                {cfg.label} · {node.level}
              </text>
              {/* Order badge */}
              <rect x={118} y={6} width={24} height={14} rx={4} fill="rgba(255,255,255,0.07)" />
              <text x={130} y={17} fill="#64748b" fontSize={9} fontFamily="JetBrains Mono" fontWeight="600" textAnchor="middle">
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
  const { learningPath, profile, learningScore, refresh } = useFlaskData();
  const [selected, setSelected] = useState(null);
  const [saving, setSaving] = useState(false);
  const [topicResources, setTopicResources] = useState(null);
  const [videoModal, setVideoModal] = useState({ open: false, video: null });
  const [errorMessage, setErrorMessage] = useState('');

  const nodes = layoutNodes(learningPath);

  // Auto-select recommended
  useEffect(() => {
    const rec = learningPath.find(s => s.status === 'recommended') || learningPath.find(s => s.status !== 'locked');
    if (rec) setSelected(rec);
  }, [learningPath]);

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
    } catch (error) {
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
      setErrorMessage(err.message || 'Unable to start video tracking.');
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
      setErrorMessage(err.message || 'Unable to track video progress.');
    }
  };

  const handleCourseAction = async (course, action) => {
    if (!selected) return;
    try {
      await apiFetch('/api/path/course/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: selected.topic, url: course.url, action }),
      });
      await refresh();
    } catch (err) {
      console.error('Course action failed:', err);
      setErrorMessage(err.message || 'Unable to track course action.');
    }
  };

  useEffect(() => {
    if (selected) {
      fetchTopicResources(selected.topic);
    }
  }, [selected]);

  const displayedResources = topicResources || selected;
  const completedCount = learningPath.filter(s => s.status === 'completed').length;
  const completionPct = profile?.pathMetrics?.topic_completion_pct ?? (learningPath.length ? Math.round((completedCount / learningPath.length) * 100) : 0);

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Map size={18} className="text-cyan-400" />
            <h1 className="font-display font-bold text-2xl text-white">Learning Path</h1>
          </div>
          <p className="text-slate-500 text-sm">Topics ordered by prerequisites — click a node to explore</p>
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

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Graph */}
        <div className="xl:col-span-2 glass-card p-6">
          <div className="font-display font-semibold text-white text-sm mb-4">Topic Dependency Graph</div>
          <SVGGraph nodes={nodes} onSelect={setSelected} selected={selected} />

          {/* Progress bar */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400">Path Progress</span>
              <span className="text-cyan-400 font-mono">
                {completedCount} / {learningPath.length} completed · score {learningScore}%
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
              {/* Topic header */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full animate-pulse"
                    style={{ background: STATUS_CONFIG[selected.status]?.color }} />
                  <span className="font-display font-bold text-white text-lg capitalize">{selected.topic}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="badge-chip" style={{
                    color: LEVEL_COLOR[selected.level],
                    background: `${LEVEL_COLOR[selected.level]}18`,
                    border: `1px solid ${LEVEL_COLOR[selected.level]}33`,
                  }}>{selected.level}</span>
                  <span className="text-xs text-slate-500">Step #{selected.order}</span>
                </div>
              </div>



              <div className="grid grid-cols-2 gap-2">
                <button disabled={saving} onClick={() => updateStatus(selected.topic, 'in-progress')} className="btn-cyber">Mark In Progress</button>
                <button disabled={saving} onClick={() => updateStatus(selected.topic, 'completed')} className="btn-cyber-solid">Mark Completed</button>
              </div>
              {errorMessage && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                  {errorMessage}
                </div>
              )}
              <div className="text-[11px] text-slate-500">Updating your path also updates the adaptive learning score and unlocks the next topic.</div>

              {/* Mini project */}
              <div className="p-3 rounded-xl bg-purple-400/6 border border-purple-400/20">
                <div className="text-xs text-purple-400 font-semibold mb-1">🎯 Mini Project</div>
                <div className="text-slate-300 text-xs leading-relaxed">{selected.project}</div>
              </div>

              {/* Prerequisites */}
              {selected.prerequisites?.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Prerequisites</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.prerequisites.map(p => (
                      <span key={p} className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-400 text-xs font-mono capitalize">{p}</span>
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
                      <button key={i} type="button" onClick={() => handleOpenVideo(v)}
                        className="w-full text-left flex items-start gap-2 p-2.5 rounded-xl bg-white/4 border border-white/8 hover:border-white/15 transition-all group">
                        <div className="w-7 h-7 rounded-lg bg-red-400/10 flex items-center justify-center flex-shrink-0">
                          <Play size={11} className="text-red-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-white text-xs font-medium leading-tight truncate group-hover:text-cyan-400 transition-colors">{v.title}</div>
                          <div className="text-slate-500 text-[10px] mt-0.5">{v.channel} · {v.duration || 'Video'}</div>
                        </div>
                        <ExternalLink size={11} className="text-slate-600 group-hover:text-cyan-400 flex-shrink-0 mt-0.5 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Courses */}
              {displayedResources?.courses?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <BookOpen size={13} className="text-cyan-400" />
                    <span className="text-xs text-slate-400 font-semibold">Related Courses</span>
                  </div>
                  <div className="space-y-2">
                    {displayedResources.courses.map((c, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => {
                          handleCourseAction(c, 'click');
                          window.open(c.url, '_blank', 'noopener');
                        }}
                        className="w-full text-left flex items-start gap-2 p-2.5 rounded-xl bg-white/4 border border-white/8 hover:border-cyan-400/20 transition-all group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-cyan-400/10 flex items-center justify-center flex-shrink-0">
                          <BookOpen size={11} className="text-cyan-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-white text-xs font-medium leading-tight truncate group-hover:text-cyan-400 transition-colors">{c.title}</div>
                          <div className="text-slate-500 text-[10px] mt-0.5">{c.provider} · ⭐ {c.rating || 'NA'}</div>
                        </div>
                        {c.certificate && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-400 flex-shrink-0">CERT</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Datasets */}
              {displayedResources?.datasets?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Layers size={13} className="text-violet-400" />
                    <span className="text-xs text-slate-400 font-semibold">Datasets</span>
                  </div>
                  <div className="space-y-2">
                    {displayedResources.datasets.map((ds, i) => (
                      <a key={i} href={ds.url} target="_blank" rel="noreferrer"
                        className="flex items-start gap-2 p-2.5 rounded-xl bg-white/4 border border-white/8 hover:border-violet-400/20 transition-all group">
                        <div className="w-7 h-7 rounded-lg bg-violet-400/10 flex items-center justify-center flex-shrink-0">
                          <span className="text-violet-400 text-xs">DS</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-white text-xs font-medium leading-tight truncate group-hover:text-cyan-400 transition-colors">{ds.title}</div>
                          <div className="text-slate-500 text-[10px] mt-0.5">{ds.source || 'Dataset'} · {ds.topic || selected.topic}</div>
                        </div>
                      </a>
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
              <div className="text-slate-500 text-sm">Click any unlocked node</div>
              <div className="text-slate-600 text-xs mt-1">to see videos, courses & project</div>
            </div>
          )}
        </div>
      </div>

      {/* Step list */}
      <div className="glass-card p-6">
        <div className="font-display font-semibold text-white text-sm mb-4">All Steps</div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {learningPath.map((step) => {
            const cfg = STATUS_CONFIG[step.status] || STATUS_CONFIG.locked;
            const StatusIcon = cfg.icon;
            return (
              <button
                key={step.topic}
                onClick={() => step.status !== 'locked' && setSelected(step)}
                disabled={step.status === 'locked'}
                className="text-left p-4 rounded-xl border transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:border-opacity-60"
                style={{
                  background: cfg.bg,
                  borderColor: cfg.border,
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <StatusIcon size={13} style={{ color: cfg.color }} />
                  <span className="font-display font-semibold text-white text-sm capitalize">{step.topic}</span>
                  <span className="ml-auto font-mono text-xs" style={{ color: cfg.color }}>#{step.order}</span>
                </div>
                <div className="text-xs text-slate-500">{cfg.label} · {step.level}</div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
