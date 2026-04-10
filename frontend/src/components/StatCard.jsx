import React from 'react';

const glowMap = {
  cyan:   'stat-glow-blue  border-cyan-400/20',
  purple: 'stat-glow-purple border-purple-400/20',
  green:  'stat-glow-green  border-emerald-400/20',
  pink:   'stat-glow-pink   border-pink-400/20',
  orange: 'border-orange-400/20',
};

const iconBgMap = {
  cyan:   'bg-cyan-400/10 text-cyan-400',
  purple: 'bg-purple-400/10 text-purple-400',
  green:  'bg-emerald-400/10 text-emerald-400',
  pink:   'bg-pink-400/10 text-pink-400',
  orange: 'bg-orange-400/10 text-orange-400',
};

export default function StatCard({ icon: Icon, label, value, sub, color = 'cyan', trend }) {
  return (
    <div className={`glass-card p-5 border ${glowMap[color]} flex flex-col gap-3`}>
      <div className="flex items-center justify-between">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${iconBgMap[color]}`}>
          <Icon size={17} />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-mono font-semibold px-2 py-0.5 rounded-full
            ${trend >= 0 ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
            {trend >= 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div>
        <div className="font-display font-bold text-2xl text-white leading-none">{value}</div>
        <div className="text-slate-400 text-sm mt-1">{label}</div>
        {sub && <div className="text-slate-600 text-xs mt-0.5 font-mono">{sub}</div>}
      </div>
    </div>
  );
}
