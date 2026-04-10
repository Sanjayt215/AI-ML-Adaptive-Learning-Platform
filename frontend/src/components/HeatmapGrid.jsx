import React, { useState } from 'react';

function scoreToColor(score) {
  if (score >= 75) return { bg: 'rgba(74,222,128,0.25)', border: 'rgba(74,222,128,0.5)', text: '#4ade80' };
  if (score >= 50) return { bg: 'rgba(251,191,36,0.2)', border: 'rgba(251,191,36,0.45)', text: '#fbbf24' };
  if (score >= 30) return { bg: 'rgba(251,146,60,0.2)', border: 'rgba(251,146,60,0.45)', text: '#fb923c' };
  return { bg: 'rgba(248,113,113,0.2)', border: 'rgba(248,113,113,0.45)', text: '#f87171' };
}

export default function HeatmapGrid({ assessment = [] }) {
  const [tooltip, setTooltip] = useState(null);

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-2">
        {assessment.map((item, i) => {
          const { bg, border, text } = scoreToColor(item.score_pct);
          const label = item.topic.length > 4 ? item.topic.slice(0, 4).toUpperCase() : item.topic.toUpperCase();
          return (
            <div
              key={i}
              className="heat-cell"
              style={{ background: bg, border: `1px solid ${border}`, color: text, width: 52, height: 52, borderRadius: 10 }}
              onMouseEnter={() => setTooltip(item)}
              onMouseLeave={() => setTooltip(null)}
            >
              <div className="flex flex-col items-center leading-tight">
                <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono', opacity: 0.85 }}>{label}</span>
                <span style={{ fontSize: 13, fontWeight: 700, fontFamily: 'Space Grotesk' }}>{item.score_pct}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="tooltip-cyber absolute -top-14 left-0 z-20 pointer-events-none">
          <div className="font-display font-semibold text-white mb-0.5">{tooltip.topic.toUpperCase()}</div>
          <div className="text-xs text-slate-400">Score: <span className="text-white font-mono">{tooltip.score_pct}%</span></div>
          <div className="text-xs text-slate-400">Level: <span className="text-white">{tooltip.predicted_level}</span></div>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
        <span className="font-mono">Legend:</span>
        {[
          { label: '≥75 Strong', color: '#4ade80' },
          { label: '50–74 OK', color: '#fbbf24' },
          { label: '30–49 Weak', color: '#fb923c' },
          { label: '<30 Critical', color: '#f87171' },
        ].map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm" style={{ background: l.color, opacity: 0.8 }} />
            <span>{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
