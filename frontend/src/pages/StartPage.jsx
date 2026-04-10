
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FileText, Target, Sparkles, ArrowRight, X } from 'lucide-react';
import { useFlaskData } from '../hooks/useFlaskData';
import { apiFetch } from '../utils/api';

const SAMPLE_TOPICS = [
  'Python', 'Data Preprocessing', 'Statistics', 'Probability', 'Feature Engineering', 'Linear Regression', 'Classification',
  'Decision Trees', 'Clustering', 'Model Evaluation', 'Naive Bayes', 'Neural Networks', 'Computer Vision', 'NLP', 'Transformers', 'LLM', 'Prompt Engineering', 'Generative AI', 'Reinforcement Learning', 'AutoML', 'Model Deployment',
];

const PRESETS = [
  { label: 'ML Basics', text: 'Python, data preprocessing, statistics, linear regression, classification, decision tree' },
  { label: 'Deep Learning', text: 'Python, neural networks, computer vision, NLP, transformers, LLM, generative AI' },
  { label: 'Full ML Stack', text: 'Python, statistics, probability, data preprocessing, feature engineering, linear regression, classification, decision trees, model evaluation, clustering, AutoML, model deployment' },
];

export default function StartPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { savePartial } = useFlaskData();
  const goalFromState = location.state?.goal;

  const [syllabusText, setSyllabusText] = useState('');
  const [targetGoal, setTargetGoal] = useState(
    goalFromState === 'placement' ? 'ML for placement prep at top tech companies' :
    goalFromState === 'project' ? 'Build a production AI project with deployment' :
    goalFromState === 'deeplearning' ? 'Master deep learning and neural networks' : ''
  );
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addTag = (topic) => {
    if (!tags.includes(topic)) setTags([...tags, topic]);
    setSyllabusText(prev => (prev ? prev + ', ' + topic : topic));
  };

  const removeTag = (t) => setTags(tags.filter(x => x !== t));

  const loadPreset = (preset) => {
    setSyllabusText(preset.text);
    setTags(preset.text.split(',').map(s => s.trim()).filter(Boolean).slice(0, 8));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!syllabusText.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ syllabus_text: syllabusText, target_goal: targetGoal }),
      });
      savePartial({ profile: data.profile, quizItems: data.quizItems, assessment: [], learningPath: [], resources: [] });
      navigate('/quiz');
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-6 py-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-400 text-xs font-mono mb-4">
          STEP 2 OF 4 · BUILD YOUR PLAN
        </div>
        <h1 className="font-display font-bold text-3xl text-white mb-2">Create your <span className="neon-text-purple">personalized</span> study plan</h1>
        <p className="text-slate-400">Paste your syllabus or topics. The quiz will be created from those selected topics only.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={15} className="text-purple-400" />
            <span className="font-display font-semibold text-white text-sm">Quick presets</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map(p => (
              <button key={p.label} type="button" onClick={() => loadPreset(p)} className="px-3 py-1.5 rounded-lg bg-purple-400/10 border border-purple-400/20 text-purple-400 text-xs font-medium hover:bg-purple-400/20 transition-colors">
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card p-5">
          <label className="block mb-2">
            <span className="font-display font-semibold text-white text-sm flex items-center gap-2"><FileText size={15} className="text-cyan-400" />Paste your syllabus or topic list</span>
            <span className="text-slate-500 text-xs mt-0.5 block">Comma separated or free text</span>
          </label>
          <textarea className="cyber-input" rows={6} value={syllabusText} onChange={e => setSyllabusText(e.target.value)} placeholder="Example: Python, data preprocessing, linear regression, decision trees, clustering, neural networks, AutoML" />

          <div className="mt-3">
            <div className="text-xs text-slate-500 mb-2">Quick add topics:</div>
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_TOPICS.map(t => (
                <button key={t} type="button" onClick={() => addTag(t)} className={`px-2.5 py-1 rounded-lg text-[11px] font-mono border transition-all ${tags.includes(t) ? 'bg-cyan-400/15 border-cyan-400/40 text-cyan-400' : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-300'}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>

          {tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {tags.map(t => (
                <span key={t} className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-xs">
                  {t}
                  <button type="button" onClick={() => removeTag(t)}><X size={10} /></button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-5">
          <label className="block mb-2">
            <span className="font-display font-semibold text-white text-sm flex items-center gap-2"><Target size={15} className="text-orange-400" />Your specific goal</span>
          </label>
          <input className="cyber-input" value={targetGoal} onChange={e => setTargetGoal(e.target.value)} placeholder="Example: I want to learn ML for placements and build real projects" />
        </div>

        {error && <div className="text-red-400 text-sm">{error}</div>}

        <div className="flex items-center justify-between">
          <div className="text-slate-500 text-xs">AI will map your selected syllabus to a custom quiz and learning path</div>
          <button type="submit" disabled={!syllabusText.trim() || loading} className={`btn-cyber-solid flex items-center gap-2 ${(!syllabusText.trim() || loading) ? 'opacity-40 cursor-not-allowed' : ''}`}>
            <Sparkles size={15} />
            {loading ? 'Generating Quiz...' : 'Analyze & Continue'}
            <ArrowRight size={15} />
          </button>
        </div>
      </form>
    </div>
  );
}
