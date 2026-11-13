import React, { useEffect, useState } from 'react';
import { Outlet, Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Brain, Search, Bell, RotateCcw, Sparkles, Play, Zap, Calendar,
  RotateCcw as RevisionIcon, Cpu, Map, Target, BookOpen, Menu, X, BarChart2,
  Activity
} from 'lucide-react';
import { apiFetch } from '../utils/api';

const NAV_LINKS = [
  { to: '/', label: 'Home', icon: Brain },
  { to: '/learn', label: 'My Learning', icon: Play },
  { to: '/learning-plan', label: 'Learning Plan', icon: Map },
  { to: '/assessments', label: 'Assessments', icon: BookOpen },
  { to: '/ai-tutor', label: 'AI Tutor', icon: Sparkles },
  { to: '/my-progress', label: 'My Progress', icon: BarChart2 },
  { to: '/resources', label: 'Resources', icon: BookOpen },
];

export default function Layout() {
  const [search, setSearch] = useState('');
  const [results, setResults] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    apiFetch('/api/notifications')
      .then(data => setNotifications(data.notifications || []))
      .catch(() => setNotifications([]));
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
    setShowSearch(false);
  }, [location.pathname]);

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
    <div className="min-h-screen text-white flex flex-col">
      {/* Primary Sticky Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl border-b border-white/10 bg-slate-950/85">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5 font-display font-bold text-lg tracking-tight shrink-0">
            <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400">
              <Brain size={18} />
            </div>
            <span>Auto<span className="text-cyan-400">Learn</span></span>
            <span className="hidden sm:inline-block text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-300 border border-cyan-400/20">
              KT-RL
            </span>
          </Link>

          {/* Desktop Search & Quick Actions */}
          <div className="flex items-center gap-2 ml-auto">
            <form onSubmit={runSearch} className="hidden lg:flex items-center gap-1.5">
              <input
                className="cyber-input text-xs py-1.5 px-3"
                style={{ width: 190 }}
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search concepts..."
              />
              <button className="btn-cyber py-1.5 px-2.5" type="submit">
                <Search size={13} />
              </button>
            </form>
            <button
              className="btn-cyber py-1.5 px-2.5 relative"
              onClick={() => setShowNotifications(s => !s)}
              title="Notifications"
            >
              <Bell size={13} />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              )}
            </button>
            <button
              className="btn-cyber py-1.5 px-2.5 text-slate-400 hover:text-white"
              onClick={resetAll}
              title="Reset Profile & Session"
            >
              <RotateCcw size={13} />
            </button>
            {/* Mobile Hamburger */}
            <button
              className="btn-cyber py-1.5 px-2.5 lg:hidden"
              onClick={() => setMobileMenuOpen(o => !o)}
            >
              {mobileMenuOpen ? <X size={15} /> : <Menu size={15} />}
            </button>
          </div>
        </div>

        {/* Student-Centric 7-Hub Navigation Bar */}
        <nav className="border-t border-white/5 bg-slate-900/60 overflow-x-auto no-scrollbar">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between gap-2 py-1.5 text-xs whitespace-nowrap">
            <div className="flex items-center gap-1">
              {NAV_LINKS.map(({ to, label, icon: Icon, badge }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                      isActive
                        ? 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-sm shadow-cyan-400/10'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`
                  }
                >
                  <Icon size={13} />
                  <span>{label}</span>
                  {badge && (
                    <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold ml-0.5">
                      {badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>

            {/* Discreet Research Mode Tab */}
            <NavLink
              to="/research/rl-intelligence"
              className={({ isActive }) =>
                `px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                    : 'text-slate-500 hover:text-purple-300 hover:bg-purple-500/10 border border-transparent'
                }`
              }
              title="Reinforcement Learning Lab & Algorithm Telemetry"
            >
              <Cpu size={12} className="text-purple-400" />
              <span>Research Mode</span>
            </NavLink>
          </div>
        </nav>
      </header>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-slate-950/95 backdrop-blur-2xl pt-24 px-6 space-y-4 overflow-y-auto">
          <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-2">Navigation</div>
          <div className="grid grid-cols-2 gap-2">
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `p-3 rounded-xl border flex items-center gap-2.5 text-xs font-semibold ${
                    isActive
                      ? 'bg-cyan-400/10 border-cyan-400/30 text-cyan-300'
                      : 'bg-white/5 border-white/5 text-slate-300'
                  }`
                }
              >
                <Icon size={14} className="text-cyan-400" />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      )}

      {/* Notifications Drawer */}
      {showNotifications && (
        <div className="max-w-7xl mx-auto px-6 pt-4 w-full">
          <div className="glass-card p-4 space-y-2 border-cyan-400/20">
            <div className="font-display font-semibold text-white text-sm flex items-center justify-between">
              <span>System & Learning Notifications</span>
              <button onClick={() => setShowNotifications(false)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            {notifications.length ? notifications.map((n, i) => (
              <div key={i} className="text-slate-300 text-xs p-2 rounded bg-white/5">
                <span className="text-cyan-400 font-semibold">{n.title}:</span> {n.message}
              </div>
            )) : <div className="text-slate-500 text-xs">No new notifications.</div>}
          </div>
        </div>
      )}

      {/* Search Overlay */}
      {showSearch && (
        <div className="max-w-7xl mx-auto px-6 pt-4 w-full">
          <div className="glass-card p-4 space-y-3 border-cyan-400/20">
            <div className="font-display font-semibold text-white text-sm flex items-center justify-between">
              <span>Search Results for "{search}"</span>
              <button onClick={() => setShowSearch(false)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            {results.length ? results.map((r, i) => (
              <a key={i} href={r.url} target="_blank" rel="noreferrer" className="block p-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition">
                <div className="text-cyan-400 text-[10px] uppercase font-mono font-bold">{r.kind} · {r.topic}</div>
                <div className="text-white text-xs font-medium">{r.title}</div>
                <div className="text-slate-500 text-[11px]">{r.provider}</div>
              </a>
            )) : <div className="text-slate-500 text-xs">No matching educational resources found.</div>}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Platform Footer */}
      <footer className="border-t border-white/5 bg-slate-950/80 mt-16 py-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Brain size={14} className="text-cyan-400" />
            <span className="text-slate-400 font-medium">AutoLearn KT-RL Platform</span>
            <span>—</span>
            <span>Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection</span>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <Link to="/rl-intelligence" className="hover:text-cyan-400 transition-colors">RL Intelligence</Link>
            <Link to="/learn" className="hover:text-cyan-400 transition-colors">Course Journey</Link>
            <Link to="/mastery" className="hover:text-cyan-400 transition-colors">Mastery Analytics</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
