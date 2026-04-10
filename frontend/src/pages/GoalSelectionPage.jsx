import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Cpu, Network, ArrowRight, Check } from 'lucide-react';

const GOALS = [
  {
    id: 'placement',
    icon: Briefcase,
    title: 'ML for Placement',
    subtitle: 'Industry Ready',
    desc: 'Master the ML concepts most asked in interviews. Focus on algorithms, optimization, and real-world problem solving for top tech companies.',
    topics: ['Python', 'Statistics', 'Linear Regression', 'Logistic Regression', 'SVM', 'Decision Trees', 'Random Forest', 'XGBoost', 'Feature Engineering', 'System Design'],
    duration: '3–4 months',
    difficulty: 'Intermediate',
    color: 'cyan',
    gradient: 'from-cyan-500/20 to-blue-500/10',
    border: 'border-cyan-400/30',
    glow: '0 0 40px rgba(0, 212, 255, 0.15)',
    badge: 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20',
  },
  {
    id: 'project',
    icon: Cpu,
    title: 'AI for Project',
    subtitle: 'Build Real Apps',
    desc: 'Build production-ready AI applications. Learn end-to-end pipelines, model deployment, and integrating ML into software products.',
    topics: ['Python', 'Data Preprocessing', 'EDA', 'Model Building', 'Flask/FastAPI', 'Docker', 'Cloud Deployment', 'MLflow', 'CI/CD', 'Monitoring'],
    duration: '2–3 months',
    difficulty: 'Beginner–Intermediate',
    color: 'purple',
    gradient: 'from-purple-500/20 to-pink-500/10',
    border: 'border-purple-400/30',
    glow: '0 0 40px rgba(168, 85, 247, 0.15)',
    badge: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  },
  {
    id: 'deeplearning',
    icon: Network,
    title: 'Deep Learning',
    subtitle: 'Neural Networks',
    desc: 'Dive into neural networks, CNNs, RNNs, Transformers, and generative models. Perfect for research, computer vision, and NLP paths.',
    topics: ['NumPy', 'PyTorch/TensorFlow', 'Neural Networks', 'CNN', 'RNN/LSTM', 'Attention Mechanism', 'Transformers', 'GANs', 'NLP', 'Model Optimization'],
    duration: '4–6 months',
    difficulty: 'Advanced',
    color: 'green',
    gradient: 'from-emerald-500/20 to-teal-500/10',
    border: 'border-emerald-400/30',
    glow: '0 0 40px rgba(52, 211, 153, 0.15)',
    badge: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  },
];

const difficultyColor = { Beginner: 'text-green-400', 'Beginner–Intermediate': 'text-yellow-400', Intermediate: 'text-yellow-400', Advanced: 'text-red-400' };

export default function GoalSelectionPage() {
  const [selected, setSelected] = useState(null);
  const navigate = useNavigate();

  const handleContinue = () => {
    if (selected) navigate('/start', { state: { goal: selected } });
  };

  return (
    <div className="px-6 py-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-400 text-xs font-mono mb-4">
          STEP 1 OF 4 · GOAL SELECTION
        </div>
        <h1 className="font-display font-bold text-3xl text-white mb-3">
          What's your <span className="neon-text-blue">learning goal?</span>
        </h1>
        <p className="text-slate-400 text-base max-w-xl mx-auto">
          Choose a track that matches your objective. Your path, resources, and quiz difficulty will be tailored accordingly.
        </p>
      </div>

      {/* Goal Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        {GOALS.map((goal) => {
          const Icon = goal.icon;
          const isSelected = selected === goal.id;
          return (
            <div
              key={goal.id}
              onClick={() => setSelected(goal.id)}
              className={`goal-card cursor-pointer relative overflow-hidden ${isSelected ? 'selected' : ''}`}
              style={{ boxShadow: isSelected ? goal.glow : undefined }}
            >
              {/* Gradient bg */}
              <div className={`absolute inset-0 bg-gradient-to-br ${goal.gradient} opacity-60 pointer-events-none`} />

              {/* Selected check */}
              {isSelected && (
                <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-cyan-400 flex items-center justify-center">
                  <Check size={14} className="text-dark-300" strokeWidth={3} />
                </div>
              )}

              <div className="relative">
                {/* Icon */}
                <div className={`w-12 h-12 rounded-2xl border flex items-center justify-center mb-5 ${goal.badge}`}>
                  <Icon size={22} />
                </div>

                {/* Subtitle badge */}
                <span className={`badge-chip ${goal.badge} border text-[10px] mb-3 inline-block`}>{goal.subtitle}</span>

                {/* Title */}
                <h2 className="font-display font-bold text-xl text-white mb-3">{goal.title}</h2>
                <p className="text-slate-400 text-sm leading-relaxed mb-5">{goal.desc}</p>

                {/* Meta */}
                <div className="flex items-center gap-4 mb-5 text-xs">
                  <div>
                    <div className="text-slate-500">Duration</div>
                    <div className="text-slate-300 font-medium mt-0.5">{goal.duration}</div>
                  </div>
                  <div className="w-px h-8 bg-white/10" />
                  <div>
                    <div className="text-slate-500">Difficulty</div>
                    <div className={`font-medium mt-0.5 ${difficultyColor[goal.difficulty] || 'text-slate-300'}`}>{goal.difficulty}</div>
                  </div>
                </div>

                {/* Topics preview */}
                <div>
                  <div className="text-xs text-slate-500 mb-2">Topics covered</div>
                  <div className="flex flex-wrap gap-1.5">
                    {goal.topics.slice(0, 6).map(t => (
                      <span key={t} className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-400 text-[11px] font-mono">
                        {t}
                      </span>
                    ))}
                    {goal.topics.length > 6 && (
                      <span className="px-2 py-0.5 rounded-md bg-white/5 text-slate-500 text-[11px]">+{goal.topics.length - 6} more</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* CTA */}
      <div className="flex items-center justify-between glass-card px-6 py-4">
        <div>
          {selected ? (
            <div>
              <div className="text-white font-display font-semibold">
                {GOALS.find(g => g.id === selected)?.title}
              </div>
              <div className="text-slate-400 text-sm">selected · ready to build your plan</div>
            </div>
          ) : (
            <div className="text-slate-400 text-sm">Select a goal to continue</div>
          )}
        </div>
        <button
          onClick={handleContinue}
          disabled={!selected}
          className={`btn-cyber-solid flex items-center gap-2 ${!selected ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          Continue
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
