import React, { useState } from 'react';
import { MessageSquare, Send, Brain, Database, BookOpen, Video } from 'lucide-react';
import { apiFetch } from '../utils/api';

const starters = [
  'What is my weakest topic and how do I improve it?',
  'Explain neural networks in simple words.',
  'Compare classification vs clustering.',
  'Suggest a dataset for model evaluation.',
  'Give me a mini project for NLP.',
  'What should I learn next?',
];

export default function TutorPage() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState(null);

  const ask = async (text) => {
    if (!text.trim()) return;
    const prompt = text.trim();
    setMessages(prev => [...prev, { role: 'user', text: prompt }]);
    setQuestion('');
    setLoading(true);
    try {
      const data = await apiFetch('/api/tutor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: prompt }),
      });
      setMeta({ mode: data.mode, topic: data.topic, retrieved: data.retrieved || [], related: data.related_resources || {} });
      setMessages(prev => [...prev, { role: 'assistant', text: data.answer || 'No answer yet.' }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: err.message || 'Start with your syllabus and quiz first.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-6 py-8 max-w-6xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2"><MessageSquare size={18} className="text-cyan-400" /><h1 className="font-display font-bold text-2xl text-white">AI Tutor</h1></div>
        <p className="text-slate-500 text-sm">Ask topic doubts, compare algorithms, request datasets, generate mini-project ideas, and get path guidance.</p>
      </div>

      <div className="grid lg:grid-cols-[1.5fr_1fr] gap-6">
        <div className="glass-card p-5">
          <div className="flex flex-wrap gap-2 mb-4">{starters.map(s => <button key={s} type="button" className="btn-cyber" onClick={() => ask(s)}>{s}</button>)}</div>
          <div className="space-y-3 mb-4 min-h-[260px]">
            {messages.length === 0 && <div className="text-slate-500 text-sm">No messages yet.</div>}
            {messages.map((m, i) => (
              <div key={i} className={`p-3 rounded-xl ${m.role === 'user' ? 'bg-cyan-400/10 text-cyan-300 ml-10' : 'bg-white/5 text-slate-300 mr-10'}`}>
                {m.text}
              </div>
            ))}
          </div>
          <form onSubmit={(e) => { e.preventDefault(); ask(question); }} className="flex gap-3">
            <input className="cyber-input" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask any AI/ML learning doubt..." />
            <button className="btn-cyber-solid" disabled={loading}><Send size={14} /></button>
          </form>
        </div>

        <div className="space-y-4">
          <div className="glass-card p-4">
            <div className="text-xs text-slate-500 mb-2">Tutor engine</div>
            <div className="flex items-center gap-2 text-white"><Brain size={16} className="text-cyan-400" />{meta?.mode || 'Ask a question to activate tutor'}</div>
            {meta?.topic && <div className="text-xs text-slate-400 mt-2">Detected topic: <span className="text-cyan-400 capitalize">{meta.topic}</span></div>}
          </div>

          <div className="glass-card p-4">
            <div className="text-xs text-slate-500 mb-3">Retrieved context</div>
            <div className="space-y-2 max-h-56 overflow-auto">
              {(meta?.retrieved || []).length ? meta.retrieved.slice(0, 5).map((item, i) => (
                <div key={i} className="p-2 rounded-lg bg-white/5 border border-white/10">
                  <div className="text-[11px] text-cyan-400 uppercase">{item.kind} · {item.topic}</div>
                  <div className="text-xs text-slate-300 line-clamp-3">{item.text}</div>
                </div>
              )) : <div className="text-slate-500 text-sm">No retrieved evidence yet.</div>}
            </div>
          </div>

          <div className="glass-card p-4 space-y-3">
            <div className="text-xs text-slate-500">Related resources</div>
            {meta?.related?.videos?.[0] && <a href={meta.related.videos[0].url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-slate-300 hover:text-cyan-400"><Video size={14} className="text-red-400" />{meta.related.videos[0].title}</a>}
            {meta?.related?.courses?.[0] && <a href={meta.related.courses[0].url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-slate-300 hover:text-cyan-400"><BookOpen size={14} className="text-cyan-400" />{meta.related.courses[0].title}</a>}
            {meta?.related?.datasets?.[0] && <a href={meta.related.datasets[0].url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-slate-300 hover:text-cyan-400"><Database size={14} className="text-green-400" />{meta.related.datasets[0].title}</a>}
            {meta?.related?.project && <div className="text-xs text-slate-400 border-t border-white/10 pt-2">Project idea: <span className="text-slate-300">{meta.related.project}</span></div>}
          </div>
        </div>
      </div>
    </div>
  );
}
