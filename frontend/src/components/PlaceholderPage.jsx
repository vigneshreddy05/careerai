import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Clock } from 'lucide-react';

export default function PlaceholderPage({
  title,
  description,
  icon: Icon,
  phaseTag = 'Phase Implementation',
  plannedFeatures = [],
}) {
  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-50 to-violet-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Icon className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60 inline-flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {phaseTag}
                </span>
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">
                {title}
              </h2>
              <p className="text-sm text-slate-500 max-w-2xl leading-relaxed">
                {description}
              </p>
            </div>
          </div>

          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors self-start md:self-center"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Planned Feature Specifications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-800">
              Planned Capabilities in this Module
            </h3>
          </div>
          <ul className="space-y-3">
            {plannedFeatures.map((feat, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-600">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                <span>{feat}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 text-white shadow-md flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-semibold tracking-wider uppercase text-indigo-300">
              Architecture Status
            </span>
            <h4 className="text-base font-bold text-white mt-1 mb-2">
              Integrated with Core AI Pipeline
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              This module is wired to our lightweight DistilBERT classification head and local Ollama Qwen 2.5 3B runtime. The backend endpoints and UI triggers will be active as we complete Phase 5 & 6.
            </p>
          </div>
          <div className="pt-4 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-400">
            <span>Deterministic ML Boundary</span>
            <span className="text-emerald-400 font-semibold">Ready for Wiring</span>
          </div>
        </div>
      </div>
    </div>
  );
}
