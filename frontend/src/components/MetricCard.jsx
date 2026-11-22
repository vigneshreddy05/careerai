import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive = true,
  accentColor = 'indigo',
  progress,
}) {
  const colorMap = {
    indigo: {
      bg: 'bg-indigo-50/80',
      text: 'text-indigo-600',
      border: 'border-indigo-100',
      bar: 'bg-indigo-600',
    },
    violet: {
      bg: 'bg-violet-50/80',
      text: 'text-violet-600',
      border: 'border-violet-100',
      bar: 'bg-violet-600',
    },
    blue: {
      bg: 'bg-blue-50/80',
      text: 'text-blue-600',
      border: 'border-blue-100',
      bar: 'bg-blue-600',
    },
    emerald: {
      bg: 'bg-emerald-50/80',
      text: 'text-emerald-600',
      border: 'border-emerald-100',
      bar: 'bg-emerald-600',
    },
  };

  const scheme = colorMap[accentColor] || colorMap.indigo;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-3 mb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            {title}
          </span>
          <div className={`p-2 rounded-xl ${scheme.bg} ${scheme.text}`}>
            <Icon className="w-4 h-4" />
          </div>
        </div>

        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {value}
          </span>
          {trend && (
            <span
              className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                trendPositive
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                  : 'bg-amber-50 text-amber-700 border border-amber-200/60'
              }`}
            >
              {trend}
            </span>
          )}
        </div>

        <p className="text-xs text-slate-500 leading-relaxed">{subtitle}</p>
      </div>

      {typeof progress === 'number' && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5 font-medium">
            <span>Score Readiness</span>
            <span className="text-slate-700 font-semibold">{progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full ${scheme.bar} rounded-full transition-all duration-500`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
