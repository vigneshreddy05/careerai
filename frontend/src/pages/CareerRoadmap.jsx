import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  ExternalLink,
  BookOpen,
  Award,
  Loader2,
  RefreshCw,
  FileText,
  Info,
  Check,
  RotateCcw,
  Sparkles,
  Bot,
  AlertCircle,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';

const AVAILABLE_BENCHMARK_ROLES = [
  'Full Stack Software Engineer',
  'Backend Software Engineer',
  'Frontend Software Engineer',
  'Cloud & DevOps Engineer',
  'Data Scientist & ML Practitioner',
  'Database Administrator & Data Engineer',
  'Software QA & Automation Engineer',
];

export default function CareerRoadmap() {
  const {
    analysisData,
    matchingData,
    roadmapData,
    isGeneratingRoadmap,
    roadmapError,
    fetchRoadmap,
    selectedTargetRole,
    setSelectedTargetRole,
  } = useResume();

  const [activeRole, setActiveRole] = useState(
    selectedTargetRole || 'Full Stack Software Engineer'
  );
  const [duration, setDuration] = useState('30-day'); // '30-day' or '60-day'
  const [completedWeeks, setCompletedWeeks] = useState([]);

  // LocalStorage storage key based on role and duration
  const storageKey = `careerai_progress_${activeRole.replace(/\s+/g, '_')}_${duration}`;

  // Safe localStorage loader
  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setCompletedWeeks(parsed);
          return;
        }
      }
      setCompletedWeeks([]);
    } catch {
      setCompletedWeeks([]);
    }
  }, [storageKey]);

  // Save progress safely
  const toggleMilestoneCompleted = (weekNum) => {
    setCompletedWeeks((prev) => {
      let updated;
      if (prev.includes(weekNum)) {
        updated = prev.filter((w) => w !== weekNum);
      } else {
        updated = [...prev, weekNum];
      }
      try {
        localStorage.setItem(storageKey, JSON.stringify(updated));
      } catch (err) {
        console.warn('Failed to save roadmap progress to localStorage:', err);
      }
      return updated;
    });
  };

  const handleResetProgress = () => {
    setCompletedWeeks([]);
    try {
      localStorage.removeItem(storageKey);
    } catch (err) {
      console.warn('Failed to remove progress from localStorage:', err);
    }
  };

  // Sync active role if selectedTargetRole changed externally (e.g. from JobRecommendations)
  useEffect(() => {
    if (selectedTargetRole && selectedTargetRole !== activeRole) {
      setActiveRole(selectedTargetRole);
    }
  }, [selectedTargetRole]);

  const customMissing = matchingData?.skill_match?.missing_skills || null;
  const missingSkillsStr =
    customMissing && Array.isArray(customMissing) ? [...customMissing].sort().join(',') : '';

  // Auto-fetch roadmap strictly when filename, role, duration, or skill gap changes
  useEffect(() => {
    if (analysisData) {
      fetchRoadmap(activeRole, duration, customMissing).catch(() => {});
    }
  }, [analysisData?.filename, activeRole, duration, missingSkillsStr, fetchRoadmap]);

  const handleRetry = () => {
    if (analysisData) {
      fetchRoadmap(activeRole, duration, customMissing, true).catch(() => {});
    }
  };

  // State 1: No Resume Uploaded Yet
  if (!analysisData) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Personalized Career Progression Roadmap
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Personalized 30-day tool ramp-up and 60-day portfolio implementation tracks.
                Distinguishes tools you already possess from targeted missing skills.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-sm">
          <div className="w-16 h-16 rounded-3xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-4 border border-slate-200/60">
            <FileText className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">
            No Resume Analyzed Yet
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6 leading-relaxed">
            Please upload and analyze a PDF or Word resume first. The roadmap engine personalizes weekly milestones based on your actual verified skills.
          </p>
          <Link
            to="/resume-analysis"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all"
          >
            <span>Analyze a Resume First</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  const roadmap = roadmapData?.roadmap;
  const milestones = roadmap?.milestones || [];
  const totalMilestones = milestones.length;
  const completedCount = completedWeeks.filter((w) => w <= totalMilestones).length;
  const progressPct =
    totalMilestones > 0 ? Math.round((completedCount / totalMilestones) * 100) : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  Personalized Career Progression Roadmap
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Phase 11 Live
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Structured timeline tailored for <strong className="text-slate-800">{activeRole}</strong> based on candidate{' '}
                <strong className="text-slate-700">{analysisData.filename}</strong>.
              </p>
            </div>
          </div>

          {/* Controls: Target Role Selector & Duration Toggle */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 self-stretch lg:self-auto">
            <select
              value={activeRole}
              onChange={(e) => {
                const newRole = e.target.value;
                setActiveRole(newRole);
                setSelectedTargetRole(newRole);
              }}
              className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
            >
              {AVAILABLE_BENCHMARK_ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>

            {/* 30-Day vs 60-Day Toggle */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/60">
              <button
                type="button"
                onClick={() => setDuration('30-day')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  duration === '30-day'
                    ? 'bg-white text-indigo-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                30-Day Intensive
              </button>
              <button
                type="button"
                onClick={() => setDuration('60-day')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  duration === '60-day'
                    ? 'bg-white text-indigo-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                60-Day Comprehensive
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Ethical Guardrail Disclaimer */}
      <div className="rounded-3xl bg-amber-50/70 border border-amber-200/80 p-5 sm:p-6 shadow-sm flex items-start gap-3.5">
        <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <h5 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-0.5">
            Ethical Growth Advisory
          </h5>
          <p className="text-xs text-amber-900/80 leading-relaxed">
            {roadmap?.ethical_disclaimer ||
              'This roadmap focuses on foundational tool proficiency and practical hands-on portfolio implementation. It does not promise hiring, job placement, or senior-level expertise within 30 or 60 days.'}
          </p>
        </div>
      </div>

      {/* Error Alert with Retry Action */}
      {roadmapError && (
        <div className="rounded-3xl bg-rose-50 border border-rose-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wider">
                Roadmap Generation Failed
              </h4>
              <p className="text-xs text-rose-700 mt-1">{roadmapError}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRetry}
            disabled={isGeneratingRoadmap}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-bold shadow-sm transition-all self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingRoadmap ? 'animate-spin' : ''}`} />
            <span>Retry Generation</span>
          </button>
        </div>
      )}

      {/* Progress & Skill Allocation Summary Card */}
      {roadmap && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                Target Objective Level
              </span>
              <div className="flex items-center gap-3">
                <h3 className="text-base font-bold text-slate-900">
                  {roadmap.target_level}
                </h3>
                {isGeneratingRoadmap && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-[11px] font-semibold animate-pulse">
                    <Loader2 className="w-3 h-3 animate-spin text-indigo-600" />
                    <span>Updating...</span>
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="text-[11px] font-bold text-slate-400 block">Roadmap Progress</span>
                <span className="text-base font-black text-slate-900">
                  {completedCount} of {totalMilestones} Milestones ({progressPct}%)
                </span>
              </div>
              {completedCount > 0 && (
                <button
                  type="button"
                  onClick={handleResetProgress}
                  title="Reset local completion progress"
                  className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-500 hover:text-slate-700 transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-100 border border-slate-200/60 overflow-hidden p-0.5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600 transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Skill Breakdown Grid: Existing Leveraged vs Target to Acquire */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-100">
              <span className="text-[11px] font-bold text-emerald-800 flex items-center gap-1.5 mb-2">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Existing Candidate Skills Leveraged ({roadmap.existing_skills_leveraged.length})</span>
              </span>
              <div className="flex flex-wrap gap-1.5">
                {roadmap.existing_skills_leveraged.length > 0 ? (
                  roadmap.existing_skills_leveraged.map((s) => (
                    <span
                      key={s}
                      className="px-2.5 py-0.5 rounded-lg bg-white border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-2xs"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400 italic">None overlapping core list</span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100">
              <span className="text-[11px] font-bold text-indigo-800 flex items-center gap-1.5 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                <span>Target Skills to Acquire ({roadmap.skills_to_acquire.length})</span>
              </span>
              <div className="flex flex-wrap gap-1.5">
                {roadmap.skills_to_acquire.map((s) => (
                  <span
                    key={s}
                    className="px-2.5 py-0.5 rounded-lg bg-white border border-indigo-200 text-xs font-semibold text-indigo-800 shadow-2xs"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Initial Loading State: Only shown if no roadmap is loaded yet */}
      {isGeneratingRoadmap && milestones.length === 0 && (
        <div className="max-w-2xl mx-auto py-16 text-center animate-fadeIn">
          <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-6 shadow-sm">
            <Loader2 className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            Synthesizing Personalized Milestones...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Constructing {duration === '60-day' ? '8-week' : '4-week'} structured milestones and curating verified free educational resources.
          </p>
        </div>
      )}

      {/* Weekly Milestones Timeline */}
      {milestones.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Calendar className="w-5 h-5 text-indigo-600" />
              <span>Weekly Milestone Timeline ({duration.toUpperCase()})</span>
            </h3>
            <span className="text-xs text-slate-400">
              Progress saved locally in browser
            </span>
          </div>

          <div className="space-y-5">
            {milestones.map((m) => {
              const isCompleted = completedWeeks.includes(m.week);
              return (
                <div
                  key={m.week}
                  className={`bg-white rounded-3xl border transition-all p-6 sm:p-7 shadow-sm ${
                    isCompleted
                      ? 'border-emerald-300 bg-emerald-50/20'
                      : 'border-slate-200/80 hover:border-indigo-300'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-100">
                    <div className="flex items-start gap-3.5">
                      <div
                        className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-sm shrink-0 shadow-sm border ${
                          isCompleted
                            ? 'bg-emerald-600 text-white border-emerald-600'
                            : 'bg-indigo-50 text-indigo-700 border-indigo-100'
                        }`}
                      >
                        {isCompleted ? <Check className="w-5 h-5" /> : `W${m.week}`}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                            Week {m.week} • {m.focus_area}
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-slate-900 tracking-tight mt-0.5">
                          {m.title}
                        </h4>
                      </div>
                    </div>

                    {/* Completion Checkbox */}
                    <button
                      type="button"
                      onClick={() => toggleMilestoneCompleted(m.week)}
                      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        isCompleted
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : 'bg-slate-100 hover:bg-slate-200/80 text-slate-600'
                      }`}
                    >
                      <CheckCircle2
                        className={`w-4 h-4 ${isCompleted ? 'text-emerald-600' : 'text-slate-400'}`}
                      />
                      <span>{isCompleted ? 'Completed' : 'Mark Complete'}</span>
                    </button>
                  </div>

                  {/* Body Content */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-5">
                    {/* Left Column: Objectives & Practical Exercise */}
                    <div className="space-y-4">
                      <div>
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                          Core Learning Objectives
                        </span>
                        <ul className="space-y-1.5">
                          {m.learning_objectives.map((obj, i) => (
                            <li key={i} className="text-xs text-slate-700 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                              <span className="leading-relaxed">{obj}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                          Hands-On Coding Exercise
                        </span>
                        <p className="text-xs text-slate-800 font-medium leading-relaxed">
                          {m.practical_exercise}
                        </p>
                        <div className="pt-2 border-t border-slate-200/60 flex items-start gap-1.5 text-[11px] text-slate-500">
                          <Award className="w-3.5 h-3.5 text-indigo-600 shrink-0 mt-0.5" />
                          <span>
                            <strong>Deliverable:</strong> {m.deliverable}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Right Column: Verified Free Educational Resources */}
                    <div>
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                        Verified Free Learning Materials
                      </span>
                      <div className="space-y-2.5">
                        {m.resources.map((res, i) => (
                          <a
                            key={i}
                            href={res.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-3.5 rounded-2xl border border-slate-200/80 hover:border-indigo-400 bg-white hover:bg-indigo-50/20 transition-all flex items-start justify-between gap-3 group"
                          >
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                                  {res.resource_type}
                                </span>
                                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200/60">
                                  100% Free
                                </span>
                              </div>
                              <h5 className="text-xs font-bold text-slate-900 group-hover:text-indigo-600 transition-colors truncate">
                                {res.title}
                              </h5>
                              <p className="text-[11px] text-slate-400 mt-0.5">
                                Platform: {res.platform}
                              </p>
                            </div>
                            <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 shrink-0 mt-1 transition-colors" />
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* End Capstone Portfolio Project Card */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-md">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-white shrink-0 shadow-inner">
                <Award className="w-6 h-6 text-indigo-300" />
              </div>
              <div className="space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/20 text-indigo-100 border border-white/20">
                  Capstone Portfolio Deliverable
                </span>
                <h4 className="text-base font-bold text-white tracking-tight">
                  Portfolio Capstone: {activeRole}
                </h4>
                <p className="text-xs text-indigo-100/90 leading-relaxed max-w-3xl">
                  {roadmap.capstone_project}
                </p>
              </div>
            </div>
          </div>

          {/* Forward Navigation Action to AI Career Assistant */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Need Guidance on Milestone Exercises?
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Consult CareerAI Assistant for step-by-step setup guides, code review tips, and interview preparation.
              </p>
            </div>
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all shrink-0"
            >
              <Bot className="w-4 h-4" />
              <span>Open Career Assistant</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
