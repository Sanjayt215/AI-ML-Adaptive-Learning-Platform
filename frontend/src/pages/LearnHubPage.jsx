import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Play, Zap, Calendar, RotateCcw, Brain, Sparkles, BookOpen, Clock,
  Compass, Award, Layers
} from 'lucide-react';
import TutorPage from './TutorPage';
import PersonalizedLearningJourney from '../components/PersonalizedLearningJourney';

const WORKFLOW_TABS = [
  {
    id: 'continue',
    label: 'Continue Learning',
    subtitle: 'Curriculum DAG Sequence',
    icon: Play,
    color: 'cyan',
    badge: 'STAGE-BY-STAGE',
  },
  {
    id: 'weak_topics',
    label: 'Improve Weak Topics',
    subtitle: 'Prerequisite Gap Repair',
    icon: Zap,
    color: 'purple',
    badge: 'BKT TARGETED',
  },
  {
    id: 'exam_prep',
    label: 'Prepare for an Exam',
    subtitle: 'Timed Mock & Roadmap',
    icon: Calendar,
    color: 'emerald',
    badge: 'MOCK EXAM',
  },
  {
    id: 'revision',
    label: 'Revise Previous Topics',
    subtitle: 'Spaced Retrieval Recall',
    icon: RotateCcw,
    color: 'pink',
    badge: 'FORGETTING CURVE',
  },
];

export default function LearnHubPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlMode = searchParams.get('mode');
  const urlView = searchParams.get('view');

  // Determine initial view: if mode is explicitly a workflow, default to practice, else journey
  const [activeView, setActiveView] = useState(
    urlView || (urlMode && ['continue', 'weak_topics', 'exam_prep', 'revision'].includes(urlMode) ? 'practice' : 'journey')
  );

  const [activeWorkflow, setActiveWorkflow] = useState(
    ['continue', 'weak_topics', 'exam_prep', 'revision'].includes(urlMode) ? urlMode : 'continue'
  );

  useEffect(() => {
    if (urlView) {
      setActiveView(urlView);
    } else if (urlMode && ['continue', 'weak_topics', 'exam_prep', 'revision'].includes(urlMode)) {
      setActiveView('practice');
      setActiveWorkflow(urlMode);
    }
  }, [urlView, urlMode]);

  const handleSelectView = (viewId) => {
    setActiveView(viewId);
    if (viewId === 'journey') {
      setSearchParams({ view: 'journey' });
    } else {
      setSearchParams({ view: 'practice', mode: activeWorkflow });
    }
  };

  const handleSelectWorkflow = (modeId) => {
    setActiveWorkflow(modeId);
    setSearchParams({ view: 'practice', mode: modeId });
  };

  return (
    <div className="space-y-6">
      {/* Top Header Mode Toggle */}
      <div className="max-w-7xl mx-auto px-6 pt-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/90 border border-white/10 shadow-xl backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 shrink-0">
              <Compass size={20} />
            </div>
            <div>
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block font-bold">
                INTELLIGENT LEARNING PLATFORM
              </span>
              <h2 className="font-display font-bold text-white text-base">Personalized Learning & Practice Hub</h2>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-white/10">
            <button
              onClick={() => handleSelectView('journey')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                activeView === 'journey'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Sparkles size={14} />
              10-Step Connected Journey
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/20 text-white font-mono uppercase">
                Step-by-Step
              </span>
            </button>

            <button
              onClick={() => handleSelectView('practice')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                activeView === 'practice'
                  ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-md shadow-purple-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Layers size={14} />
              Adaptive Practice Workflows
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/20 text-white font-mono uppercase">
                4 Modes
              </span>
            </button>
          </div>
        </div>

        {/* Workflow sub-bar if practice view is active */}
        {activeView === 'practice' && (
          <div className="mt-4 p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {WORKFLOW_TABS.map(tab => {
                const Icon = tab.icon;
                const isSelected = activeWorkflow === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleSelectWorkflow(tab.id)}
                    className={`p-2.5 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
                      isSelected
                        ? 'bg-cyan-400/15 border-cyan-400 text-white shadow-sm shadow-cyan-400/10'
                        : 'bg-white/5 border-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <Icon size={16} className={isSelected ? 'text-cyan-400' : 'text-slate-400'} />
                    <div className="truncate">
                      <div className="text-xs font-bold truncate">{tab.label}</div>
                      <div className="text-[10px] font-mono text-slate-500 truncate">{tab.subtitle}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {activeView === 'journey' ? (
        <PersonalizedLearningJourney />
      ) : (
        <TutorPage forcedMode={activeWorkflow} />
      )}
    </div>
  );
}
