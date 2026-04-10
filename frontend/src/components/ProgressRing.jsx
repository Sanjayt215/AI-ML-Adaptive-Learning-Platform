import React from 'react';

export default function ProgressRing({ value = 0, size = 100, stroke = 8, color = '#00d4ff', label, sublabel }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="progress-ring" viewBox={`0 0 ${size} ${size}`}>
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={stroke}
          />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none" stroke={color} strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display font-bold text-white" style={{ fontSize: size * 0.2 }}>
            {Math.round(value)}%
          </span>
        </div>
      </div>
      {label && <div className="text-xs font-display font-semibold text-white text-center">{label}</div>}
      {sublabel && <div className="text-xs text-slate-500 text-center">{sublabel}</div>}
    </div>
  );
}
