
import React, { useEffect, useState } from 'react';
import { Outlet, Link, NavLink, useNavigate } from 'react-router-dom';
import { Brain, Search, Bell, RotateCcw } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function Layout() {
  const [search, setSearch] = useState('');
  const [results, setResults] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    apiFetch('/api/notifications')
      .then(data => setNotifications(data.notifications || []))
      .catch(() => setNotifications([]));
  }, []);

  const runSearch = async (e) => {
    e?.preventDefault?.();
    if (!search.trim()) {
      setResults([]);
      setShowSearch(true);
      return;
    }

    try {
      const data = await apiFetch(`/api/search?q=${encodeURIComponent(search)}`);
      setResults(data.results || []);
    } catch {
      setResults([]);
    }
    setShowSearch(true);
  };

  const resetAll = async () => {
    await apiFetch('/api/reset', { method: 'POST' });
    sessionStorage.clear();
    navigate('/');
    window.location.reload();
  };

  return (
    <div className="min-h-screen text-white">
      <header className="sticky top-0 z-40 backdrop-blur-xl border-b border-white/10 bg-slate-950/70">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-3 font-display font-bold text-lg"><Brain className="text-cyan-400" size={22} />AutoLearn</Link>
          <nav className="hidden md:flex items-center gap-4 text-sm">
            <NavLink to="/goals">Goals</NavLink>
            <NavLink to="/start">Start</NavLink>
            <NavLink to="/quiz">Quiz</NavLink>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/path">Path</NavLink>
            <NavLink to="/resources">Resources</NavLink>
            <NavLink to="/tutor">Tutor</NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <form onSubmit={runSearch} className="hidden md:flex items-center gap-2">
              <input className="cyber-input" style={{ minWidth: 220 }} value={search} onChange={e => setSearch(e.target.value)} placeholder="Search resources" />
              <button className="btn-cyber" type="submit"><Search size={14} /></button>
            </form>
            <button className="btn-cyber" onClick={() => setShowNotifications(s => !s)}><Bell size={14} /></button>
            <button className="btn-cyber" onClick={resetAll}><RotateCcw size={14} /></button>
          </div>
        </div>
      </header>

      {showNotifications && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <div className="glass-card p-4 space-y-2">
            <div className="font-display font-semibold text-white text-sm">Notifications</div>
            {notifications.length ? notifications.map((n, i) => <div key={i} className="text-slate-300 text-sm"><span className="text-cyan-400 font-medium">{n.title}:</span> {n.message}</div>) : <div className="text-slate-500 text-sm">No notifications yet.</div>}
          </div>
        </div>
      )}

      {showSearch && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <div className="glass-card p-4 space-y-3">
            <div className="font-display font-semibold text-white text-sm">Search Results</div>
            {results.length ? results.map((r, i) => (
              <a key={i} href={r.url} target="_blank" rel="noreferrer" className="block p-3 rounded-xl bg-white/5 hover:bg-white/10 transition">
                <div className="text-cyan-400 text-xs uppercase">{r.kind} · {r.topic}</div>
                <div className="text-white text-sm">{r.title}</div>
                <div className="text-slate-500 text-xs">{r.provider}</div>
              </a>
            )) : <div className="text-slate-500 text-sm">No results found.</div>}
          </div>
        </div>
      )}

      <main><Outlet /></main>
    </div>
  );
}
