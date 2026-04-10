import React, { useState } from 'react';
import { FolderOpen, Play, BookOpen, Database, Wrench, ExternalLink, Filter, Star, Award, ChevronDown } from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';

const LEVEL_BADGE = {
  beginner:     { color: '#4ade80', bg: 'rgba(74,222,128,0.12)',   border: 'rgba(74,222,128,0.3)' },
  intermediate: { color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',   border: 'rgba(251,191,36,0.3)' },
  advanced:     { color: '#f87171', bg: 'rgba(248,113,113,0.12)',  border: 'rgba(248,113,113,0.3)' },
};

function youtubeEmbed(url) {
  if (!url) return '';
  const m = url.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{6,})/);
  return m ? `https://www.youtube.com/embed/${m[1]}` : url;
}

function VideoCard({ video }) {
  const embedUrl = youtubeEmbed(video.url);
  const [showEmbed, setShowEmbed] = useState(false);
  return (
    <div className="resource-card">
      {showEmbed ? (
        <div className="aspect-video">
          <iframe
            src={embedUrl}
            title={video.title}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      ) : (
        <button
          onClick={() => setShowEmbed(true)}
          className="w-full aspect-video bg-red-900/10 flex flex-col items-center justify-center gap-3 group hover:bg-red-900/20 transition-colors"
        >
          <div className="w-14 h-14 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Play size={22} className="text-red-400 ml-1" />
          </div>
          <span className="text-slate-400 text-xs">Click to play</span>
        </button>
      )}
      <div className="p-3">
        <a href={video.url} target="_blank" rel="noreferrer"
          className="font-display font-semibold text-white text-sm hover:text-cyan-400 transition-colors leading-tight block mb-1">
          {video.title}
        </a>
        <div className="text-slate-500 text-xs flex items-center gap-2">
          <span>{video.channel}</span>
          {video.duration && <><span>·</span><span>{video.duration}</span></>}
          {video.viewCount && <><span>·</span><span>{video.viewCount} views</span></>}
        </div>
      </div>
    </div>
  );
}

function CourseCard({ course }) {
  const lvl = LEVEL_BADGE[course.level] || LEVEL_BADGE.beginner;
  return (
    <a href={course.url} target="_blank" rel="noreferrer" className="resource-card p-4 block group hover:no-underline">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="w-9 h-9 rounded-xl bg-cyan-400/10 flex items-center justify-center flex-shrink-0">
          <BookOpen size={16} className="text-cyan-400" />
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          {course.certificate && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-400 flex items-center gap-1">
              <Award size={8} /> CERT
            </span>
          )}
          {course.verified && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-green-400/10 border border-green-400/30 text-green-400">✓ VER</span>
          )}
        </div>
      </div>
      <div className="font-display font-semibold text-white text-sm leading-tight group-hover:text-cyan-400 transition-colors mb-1">
        {course.title}
      </div>
      <div className="text-slate-500 text-xs mb-2">{course.provider}</div>
      <div className="flex items-center gap-3 text-xs flex-wrap">
        {course.rating && (
          <div className="flex items-center gap-1 text-yellow-400">
            <Star size={10} fill="currentColor" />
            <span className="font-mono font-semibold">{course.rating}</span>
          </div>
        )}
        {course.learners && <span className="text-slate-500">{course.learners} learners</span>}
        {course.duration_hours && <span className="text-slate-500">{course.duration_hours}h</span>}
        <span className="px-1.5 py-0.5 rounded-md text-[10px]"
          style={{ color: lvl.color, background: lvl.bg, border: `1px solid ${lvl.border}` }}>
          {course.level}
        </span>
      </div>
    </a>
  );
}

function DatasetCard({ dataset }) {
  const lvl = LEVEL_BADGE[dataset.level] || LEVEL_BADGE.beginner;
  return (
    <a href={dataset.url} target="_blank" rel="noreferrer" className="resource-card p-4 block group">
      <div className="flex items-start gap-3 mb-2">
        <div className="w-8 h-8 rounded-xl bg-blue-400/10 flex items-center justify-center flex-shrink-0">
          <Database size={14} className="text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-display font-semibold text-white text-sm leading-tight group-hover:text-cyan-400 transition-colors truncate">
            {dataset.title}
          </div>
          <div className="text-slate-500 text-xs mt-0.5 flex items-center gap-2">
            <span>{dataset.source}</span>
            <span className="px-1.5 py-0.5 rounded text-[10px]"
              style={{ color: lvl.color, background: lvl.bg }}>
              {dataset.level}
            </span>
          </div>
        </div>
        <ExternalLink size={12} className="text-slate-600 group-hover:text-cyan-400 flex-shrink-0 mt-0.5 transition-colors" />
      </div>
      <div className="text-slate-400 text-xs leading-relaxed">{dataset.description}</div>
    </a>
  );
}

export default function ResourcesPage() {
  const { resources } = useFlaskData();
  const [selectedTopic, setSelectedTopic] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');
  const [activeSection, setActiveSection] = useState({});

  const topics = ['all', ...resources.map(r => r.topic)];

  const filtered = resources.filter(r => {
    if (selectedTopic !== 'all' && r.topic !== selectedTopic) return false;
    if (levelFilter !== 'all' && r.level !== levelFilter) return false;
    return true;
  });

  const toggleSection = (topic, section) => {
    setActiveSection(s => ({ ...s, [`${topic}_${section}`]: !s[`${topic}_${section}`] }));
  };

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FolderOpen size={20} className="text-cyan-400" />
        <div>
          <h1 className="font-display font-bold text-2xl text-white">Learning Resources</h1>
          <p className="text-slate-500 text-sm">Videos, courses, datasets & projects — ranked for your level</p>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Filter size={14} />
          <span className="font-display font-medium">Filters</span>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Topic</label>
            <select
              className="cyber-select"
              value={selectedTopic}
              onChange={e => setSelectedTopic(e.target.value)}
            >
              {topics.map(t => <option key={t} value={t}>{t === 'all' ? 'All Topics' : t}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Level</label>
            <select
              className="cyber-select"
              value={levelFilter}
              onChange={e => setLevelFilter(e.target.value)}
            >
              {['all', 'beginner', 'intermediate', 'advanced'].map(l =>
                <option key={l} value={l}>{l === 'all' ? 'All Levels' : l}</option>
              )}
            </select>
          </div>
        </div>
        <div className="ml-auto text-xs text-slate-500 font-mono">{filtered.length} topic{filtered.length !== 1 ? 's' : ''} shown</div>
      </div>

      {/* Resource cards per topic */}
      {filtered.length === 0 && (
        <div className="glass-card p-12 text-center">
          <FolderOpen size={36} className="text-slate-600 mx-auto mb-3" />
          <div className="text-slate-400">No resources match your filters</div>
        </div>
      )}

      {filtered.map(card => {
        const lvl = LEVEL_BADGE[card.level] || LEVEL_BADGE.beginner;
        return (
          <div key={card.topic} className="glass-card overflow-hidden">
            {/* Card header */}
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-400/20 flex items-center justify-center">
                  <BookOpen size={16} className="text-cyan-400" />
                </div>
                <div>
                  <div className="font-display font-bold text-white capitalize">{card.topic}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs px-2 py-0.5 rounded-full border"
                      style={{ color: lvl.color, background: lvl.bg, borderColor: lvl.border }}>
                      {card.level}
                    </span>
                    <span className="text-xs text-slate-600 font-mono">{card.video_source}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Mini project */}
            {card.project && (
              <div className="px-6 py-3 bg-purple-400/5 border-b border-white/10 flex items-start gap-2">
                <Wrench size={13} className="text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="text-purple-400 text-xs font-semibold mr-2">Mini Project:</span>
                  <span className="text-slate-300 text-xs">{card.project}</span>
                </div>
              </div>
            )}

            <div className="p-6 space-y-6">
              {/* Videos */}
              {card.videos?.length > 0 && (
                <div>
                  <button
                    onClick={() => toggleSection(card.topic, 'videos')}
                    className="flex items-center gap-2 mb-3 group"
                  >
                    <Play size={14} className="text-red-400" />
                    <span className="font-display font-semibold text-white text-sm">Videos</span>
                    <span className="text-slate-500 text-xs">({card.videos.length})</span>
                    <ChevronDown size={14} className={`text-slate-500 transition-transform ml-1 ${activeSection[`${card.topic}_videos`] ? '' : 'rotate-180'}`} />
                  </button>
                  {!activeSection[`${card.topic}_videos`] && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {card.videos.map((v, i) => <VideoCard key={i} video={v} />)}
                    </div>
                  )}
                </div>
              )}

              {/* Courses */}
              {card.courses?.length > 0 && (
                <div>
                  <button
                    onClick={() => toggleSection(card.topic, 'courses')}
                    className="flex items-center gap-2 mb-3"
                  >
                    <BookOpen size={14} className="text-cyan-400" />
                    <span className="font-display font-semibold text-white text-sm">Verified Courses</span>
                    <span className="text-slate-500 text-xs">({card.courses.length})</span>
                    <ChevronDown size={14} className={`text-slate-500 transition-transform ml-1 ${activeSection[`${card.topic}_courses`] ? '' : 'rotate-180'}`} />
                  </button>
                  {!activeSection[`${card.topic}_courses`] && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {card.courses.map((c, i) => <CourseCard key={i} course={c} />)}
                    </div>
                  )}
                </div>
              )}

              {/* Datasets */}
              {card.datasets?.length > 0 && (
                <div>
                  <button
                    onClick={() => toggleSection(card.topic, 'datasets')}
                    className="flex items-center gap-2 mb-3"
                  >
                    <Database size={14} className="text-blue-400" />
                    <span className="font-display font-semibold text-white text-sm">Kaggle Datasets</span>
                    <span className="text-slate-500 text-xs">({card.datasets.length})</span>
                    <ChevronDown size={14} className={`text-slate-500 transition-transform ml-1 ${activeSection[`${card.topic}_datasets`] ? '' : 'rotate-180'}`} />
                  </button>
                  {!activeSection[`${card.topic}_datasets`] && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {card.datasets.map((d, i) => <DatasetCard key={i} dataset={d} />)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
