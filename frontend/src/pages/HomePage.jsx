import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap, Brain, TrendingUp, Map, BookOpen, MessageSquare, ArrowRight,
  Star, Users, Award, Play, RotateCcw, Calendar, CheckCircle2,
  Cpu, Activity, Layers, Sparkles, Shield, AlertTriangle
} from 'lucide-react';
import { apiFetch } from '../utils/api';

const FEATURES = [
  { icon: Brain, title: 'AI Assessment', desc: 'Adaptive quizzes that measure your real knowledge level across topics.', color: 'cyan' },
  { icon: TrendingUp, title: 'Progress Analytics', desc: 'Visual heatmaps and accuracy trends to track your learning journey.', color: 'purple' },
  { icon: Map, title: 'Smart Learning Path', desc: 'Topic graph with prerequisites, guiding you in the correct order.', color: 'green' },
  { icon: MessageSquare, title: 'AI Tutor Chat', desc: 'Ask doubts about AI/ML topics, get simple explanations, project ideas, and personalized guidance.', color: 'pink' },
  { icon: BookOpen, title: 'Curated Resources', desc: 'YouTube videos, verified courses, Kaggle datasets, and mini projects.', color: 'orange' },
  { icon: Award, title: 'Certificate Paths', desc: 'Structured programs for placements, projects, and deep learning goals.', color: 'cyan' },
];

const colorMap = {
  cyan: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
  purple: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
  green: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  pink: 'text-pink-400 bg-pink-400/10 border-pink-400/20',
  orange: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
};

export default function HomePage() {
  const [intel, setIntel] = useState(null);

  useEffect(() => {
    apiFetch('/api/learner/intelligence')
      .then((data) => {
        if (data && data.ok) setIntel(data);
      })
      .catch(() => {});
  }, []);

  const overallMastery = intel?.knowledge_state?.overall_mastery_pct || 68;
  const masteredCount = intel?.knowledge_state?.mastered_kcs_count || 12;
  const totalKcs = intel?.knowledge_state?.total_kcs || 30;
  const retentionPct = intel?.retention_estimates?.average_retention_pct || 88;

  return (
    <div className="px-6 py-8 max-w-6xl mx-auto space-y-12">
      {/* Hero */}
      <div className="relative rounded-3xl overflow-hidden border border-white/10 bg-slate-950/80">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/15 via-purple-500/10 to-transparent" />
        <div className="absolute inset-0 grid-bg opacity-40" />

        {/* Floating background glows */}
        <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-cyan-400/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-80 h-80 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

        <div className="relative p-10 lg:p-14">
          <div className="flex items-center gap-2 mb-6">
            <span className="px-3.5 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs font-mono font-semibold tracking-wider flex items-center gap-1.5">
              <Sparkles size={13} />
              AI & REINFORCEMENT LEARNING POWERED
            </span>
            <span className="px-3 py-1 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-300 text-xs font-mono">
              BKT · DUELING DQN · LINUCB
            </span>
          </div>

          <h1 className="font-display font-bold text-4xl lg:text-5xl text-white leading-tight mb-5 max-w-3xl">
            Adaptive AI and ML,RL Learning,{' '}
            <span className="neon-text-blue">Personalized</span>{' '}
            For Your Goals
          </h1>

          <p className="text-slate-300 text-lg leading-relaxed max-w-2xl mb-8">
            An intelligent learning companion that understands your knowledge, adapts your practice and helps you achieve lasting mastery.
          </p>

          <div className="flex flex-wrap gap-4">
            <Link to="/learn?view=journey" className="btn-cyber-solid flex items-center gap-2 text-sm font-bold shadow-lg shadow-cyan-500/20">
              <Sparkles size={16} />
              Start 10-Step Personalized Journey
            </Link>
            <Link to="/learn?view=practice" className="btn-cyber flex items-center gap-2 text-sm">
              <Layers size={16} className="text-cyan-400" />
              Adaptive Practice Workflows
            </Link>
            <Link to="/assessments" className="btn-cyber flex items-center gap-2 text-sm">
              <BookOpen size={16} className="text-cyan-400" />
              Assessments Hub
            </Link>
          </div>

          {/* Live Learner Intelligence Preview Banner */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-10 pt-8 border-t border-white/10">
            <div>
              <div className="font-display font-bold text-white text-2xl leading-none text-cyan-400">
                {overallMastery}%
              </div>
              <div className="text-slate-400 text-xs mt-1 font-medium">BKT Mastery Index</div>
            </div>
            <div>
              <div className="font-display font-bold text-white text-2xl leading-none text-emerald-400">
                {masteredCount}/{totalKcs}
              </div>
              <div className="text-slate-400 text-xs mt-1 font-medium">Concepts Mastered</div>
            </div>
            <div>
              <div className="font-display font-bold text-white text-2xl leading-none text-purple-400">
                {retentionPct}%
              </div>
              <div className="text-slate-400 text-xs mt-1 font-medium">Memory Retention R(t)</div>
            </div>
            <div>
              <div className="font-display font-bold text-white text-2xl leading-none text-amber-400">
                52 Actions
              </div>
              <div className="text-slate-400 text-xs mt-1 font-medium">Topological Action Mask</div>
            </div>
          </div>
        </div>
      </div>

      {/* 10-Step Connected Journey Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-cyan-950/40 via-slate-900/80 to-purple-950/40 border border-cyan-500/20 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-400/20 text-cyan-300 text-[10px] font-mono font-bold uppercase tracking-wider">
                Full Learning Journey
              </span>
              <span className="text-slate-400 text-xs">Diagnostic → Mastery → Mock Exam</span>
            </div>
            <h2 className="text-xl font-display font-bold text-white">
              Targeted 10-Step Intelligent Student Journey
            </h2>
            <p className="text-slate-300 text-xs max-w-2xl leading-relaxed">
              Diagnose existing mastery without penalties, review detailed topic-wise gaps, learn concepts with step-by-step explanations & formulas, practice across 7 active learning methods, and prove readiness through multi-format mock exams.
            </p>
          </div>
          <Link
            to="/learn?view=journey"
            className="btn-cyber-solid shrink-0 flex items-center justify-center gap-2 text-sm font-bold shadow-lg shadow-cyan-500/20 px-6 py-3"
          >
            <Sparkles size={16} />
            Launch 10-Step Journey
            <ArrowRight size={16} />
          </Link>
        </div>

        {/* Mini 6-stage roadmap bar */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mt-6 pt-5 border-t border-white/5">
          {[
            { step: '01', title: 'Diagnostic Quiz', desc: 'Baseline Assessment' },
            { step: '02', title: 'Knowledge Report', desc: 'Topic-Wise Mastery' },
            { step: '03', title: 'Weak Prioritization', desc: 'Identified Gaps' },
            { step: '04', title: 'Concept Teaching', desc: 'Why & How It Works' },
            { step: '05', title: '7 Learning Modes', desc: 'Code & Recall' },
            { step: '06', title: 'Mock Examination', desc: 'Multi-Method Validation' },
          ].map((item, idx) => (
            <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-white/5">
              <div className="text-[10px] font-mono text-cyan-400 font-bold">{item.step}</div>
              <div className="text-xs font-bold text-white truncate mt-0.5">{item.title}</div>
              <div className="text-[10px] text-slate-400 truncate">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Four Core Personalized Learning Modules */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-6 bg-cyan-400 rounded-full" />
            <h2 className="font-display font-bold text-white text-2xl">Personalized Learning Modules</h2>
          </div>
          <span className="badge-chip text-xs text-cyan-400 bg-cyan-400/10 border border-cyan-400/20">
            4 Distinct Pedagogical Workflows
          </span>
        </div>
        <p className="text-slate-400 text-sm mb-6 ml-3 max-w-3xl">
          Each module executes an isolated decision objective powered by the shared Bayesian learner intelligence layer.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* 1. Continue Learning */}
          <Link
            to="/learn?mode=continue"
            className="glass-card p-6 group hover:border-cyan-400/50 transition-all hover:-translate-y-1.5 duration-300 block flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-105 transition-transform">
                <Play size={22} />
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold block mb-1">
                Workflow A
              </span>
              <h3 className="font-display font-bold text-white text-lg mb-2 group-hover:text-cyan-300 transition-colors">
                Continue Learning
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed mb-4">
                Adaptive course journey. The DAG topological planner identifies your next prerequisite-eligible milestone and serves calibrated exercises.
              </p>
            </div>
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-cyan-400 font-semibold">
              <span>Resume Course Journey</span>
              <ArrowRight size={14} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </Link>

          {/* 2. Improve My Weak Topics */}
          <Link
            to="/learn?mode=weak_topics"
            className="glass-card p-6 group hover:border-red-400/50 transition-all hover:-translate-y-1.5 duration-300 block flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-red-400/10 border border-red-400/20 flex items-center justify-center text-red-400 mb-4 group-hover:scale-105 transition-transform">
                <Zap size={22} />
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-red-400 font-bold block mb-1">
                Workflow B
              </span>
              <h3 className="font-display font-bold text-white text-lg mb-2 group-hover:text-red-300 transition-colors">
                Improve Weak Topics
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed mb-4">
                Intelligent remedial studio. Automatically diagnoses low BKT mastery (P(L) &lt; 0.70) and repairs upstream prerequisite gaps.
              </p>
            </div>
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-red-400 font-semibold">
              <span>Repair Knowledge Gaps</span>
              <ArrowRight size={14} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </Link>

          {/* 3. Prepare for an Exam */}
          <Link
            to="/learn?mode=exam_prep"
            className="glass-card p-6 group hover:border-purple-400/50 transition-all hover:-translate-y-1.5 duration-300 block flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-purple-400/10 border border-purple-400/20 flex items-center justify-center text-purple-400 mb-4 group-hover:scale-105 transition-transform">
                <Calendar size={22} />
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-bold block mb-1">
                Workflow C
              </span>
              <h3 className="font-display font-bold text-white text-lg mb-2 group-hover:text-purple-300 transition-colors">
                Prepare for an Exam
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed mb-4">
                Exam preparation command center. Dynamic day-by-day roadmap, countdown timer, syllabus readiness %, and full Timed Mock Exam simulation.
              </p>
            </div>
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-purple-400 font-semibold">
              <span>Open Exam Command Center</span>
              <ArrowRight size={14} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </Link>

          {/* 4. Revise Previous Topics */}
          <Link
            to="/learn?mode=revision"
            className="glass-card p-6 group hover:border-emerald-400/50 transition-all hover:-translate-y-1.5 duration-300 block flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-emerald-400/10 border border-emerald-400/20 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-105 transition-transform">
                <RotateCcw size={22} />
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block mb-1">
                Workflow D
              </span>
              <h3 className="font-display font-bold text-white text-lg mb-2 group-hover:text-emerald-300 transition-colors">
                Revision Center
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed mb-4">
                Long-term memory retention center. Spaced retrieval with half-life decay R(t) = 2^(-Δt/S), due queues, and interactive flashcards.
              </p>
            </div>
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-emerald-400 font-semibold">
              <span>Start Spaced Retrieval</span>
              <ArrowRight size={14} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </Link>
        </div>
      </div>

      {/* Grounded Adaptive Recommendation Example Card */}
      <div className="glass-card p-6 border-cyan-400/30 bg-cyan-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <Sparkles className="text-cyan-400" size={20} />
            <div>
              <h3 className="text-white font-display font-bold text-base">Example Grounded RL Decision</h3>
              <p className="text-slate-400 text-xs">Transparent reasoning displayed to students for every action.</p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-400/10 text-cyan-300 border border-cyan-400/20">
            Policy: Composite Adaptive (BKT + Recovery)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-5 text-xs">
          <div className="space-y-1.5">
            <span className="font-mono text-slate-400 uppercase tracking-wider text-[11px] block">Selected Activity</span>
            <div className="text-white font-bold text-sm">Level 2 Exercise: NumPy Vectorized Indexing</div>
            <p className="text-slate-400 leading-relaxed">
              Targeted practice testing ndarray slicing, boolean indexing, and memory stride alignment.
            </p>
          </div>

          <div className="space-y-1.5">
            <span className="font-mono text-slate-400 uppercase tracking-wider text-[11px] block">Knowledge Evidence</span>
            <div className="text-amber-400 font-bold text-sm">P(Mastery) = 0.42 · Consecutive Errors = 1</div>
            <p className="text-slate-400 leading-relaxed">
              Learner made an indexing error on multidimensional slice; foundational syntax is mastered (P(L) = 0.88).
            </p>
          </div>

          <div className="space-y-1.5">
            <span className="font-mono text-slate-400 uppercase tracking-wider text-[11px] block">Pedagogical Objective</span>
            <div className="text-emerald-400 font-bold text-sm">Zone of Proximal Development Calibration</div>
            <p className="text-slate-400 leading-relaxed">
              Calibrated step avoids frustration downshift while reinforcing core indexing semantics before tensor operations.
            </p>
          </div>
        </div>
      </div>

      {/* The Closed-Loop Reinforcement Learning Process */}
      <div className="glass-card p-8 space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">Under The Hood</span>
          <h2 className="text-2xl font-display font-bold text-white">The AutoLearn Closed-Loop RL Engine</h2>
          <p className="text-slate-400 text-xs leading-relaxed">
            Every submission triggers Bayesian Knowledge Tracing updates, topological action masking, and multi-objective policy evaluation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2 text-xs">
            <div className="w-8 h-8 rounded-lg bg-cyan-400/10 flex items-center justify-center text-cyan-400 font-bold font-mono">1</div>
            <h4 className="font-bold text-white text-sm">Student Interaction</h4>
            <p className="text-slate-400 leading-relaxed">
              Answer selection and validated response time (ms) captured into the SQLite learning event store.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2 text-xs">
            <div className="w-8 h-8 rounded-lg bg-purple-400/10 flex items-center justify-center text-purple-400 font-bold font-mono">2</div>
            <h4 className="font-bold text-white text-sm">BKT State Update</h4>
            <p className="text-slate-400 leading-relaxed">
              Bayesian Knowledge Tracing updates posterior probability P(L_t) using slip, guess, and transition parameters.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2 text-xs">
            <div className="w-8 h-8 rounded-lg bg-emerald-400/10 flex items-center justify-center text-emerald-400 font-bold font-mono">3</div>
            <h4 className="font-bold text-white text-sm">Topological Action Mask</h4>
            <p className="text-slate-400 leading-relaxed">
              Curriculum DAG masks out unready concepts, ensuring the agent only selects prerequisite-eligible exercises.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2 text-xs">
            <div className="w-8 h-8 rounded-lg bg-amber-400/10 flex items-center justify-center text-amber-400 font-bold font-mono">4</div>
            <h4 className="font-bold text-white text-sm">Multi-Objective Selection</h4>
            <p className="text-slate-400 leading-relaxed">
              Policy balances learning gain, information gain (EIG bits), ZPD challenge match, and frustration avoidance.
            </p>
          </div>
        </div>
      </div>

      {/* Platform Features Grid */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-5 bg-purple-400 rounded-full" />
          <h2 className="font-display font-semibold text-white text-xl">Platform Capabilities</h2>
        </div>
        <p className="text-slate-400 text-sm mb-6 ml-3">Everything you need to achieve comprehensive machine learning mastery</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="glass-card p-5 group hover:-translate-y-1 transition-all duration-300">
              <div className={`w-10 h-10 rounded-xl border flex items-center justify-center mb-4 ${colorMap[color]}`}>
                <Icon size={18} />
              </div>
              <h3 className="font-display font-semibold text-white text-sm mb-2">{title}</h3>
              <p className="text-slate-400 text-xs leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
