import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Compass,
  FileText,
  Loader2,
  RefreshCw,
  Info,
  Check,
  Plus,
  Layers,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';

export default function JobRecommendations() {
  const navigate = useNavigate();
  const {
    analysisData,
    predictionData,
    recommendationsData,
    isRecommending,
    recommendationsError,
    fetchRecommendations,
    setSelectedTargetRole,
  } = useResume();

  const [activeTab, setActiveTab] = useState('all'); // 'all', 'strong', 'alternative'

  useEffect(() => {
    if (analysisData && !recommendationsData && !isRecommending && !recommendationsError) {
      fetchRecommendations().catch(() => {});
    }
  }, [analysisData, recommendationsData, isRecommending, recommendationsError, fetchRecommendations]);

  const handleSelectRoleForRoadmap = (roleTitle) => {
    setSelectedTargetRole(roleTitle);
    navigate('/roadmap');
  };

  // State 1: No Resume Uploaded Yet
  if (!analysisData) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Personalized Career Recommendations
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Synthesizes your parsed technical skills, years of experience, and DistilBERT category classifications
                to recommend high-affinity career trajectories and lateral expansion paths.
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
            Please upload and analyze a PDF or Word resume first. The recommendation engine consumes your verified skills and classification profile in memory.
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

  // State 2: Loading State
  if (isRecommending && !recommendationsData) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center animate-fadeIn">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-6 shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">
          Generating Career Recommendations...
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          Evaluating your {analysisData.skills?.all_skills?.length || 0} verified skills and classification affinities against benchmark career pathways.
        </p>
      </div>
    );
  }

  const recommendations = recommendationsData?.recommendations || [];
  const strongMatches = recommendations.filter((r) => r.match_type === 'Strong Match');
  const alternativePaths = recommendations.filter((r) => r.match_type === 'Alternative Career Path');
  const exploratoryTracks = recommendations.filter((r) => r.match_type === 'Exploratory Track');

  const filteredRoles =
    activeTab === 'strong'
      ? strongMatches
      : activeTab === 'alternative'
      ? alternativePaths
      : activeTab === 'exploratory'
      ? exploratoryTracks
      : recommendations;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  Personalized Career Recommendations
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Phase 11 Live
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Derived from verified candidate resume: <strong className="text-slate-700">{analysisData.filename}</strong> (
                {analysisData.skills?.all_skills?.length || 0} technical skills detected).
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => fetchRecommendations()}
            disabled={isRecommending}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRecommending ? 'animate-spin' : ''}`} />
            <span>Refresh Analysis</span>
          </button>
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
            {recommendationsData?.disclaimer ||
              'This roadmap focuses on foundational tool proficiency and practical hands-on portfolio implementation. It does not promise hiring, job placement, or senior-level expertise within 30 or 60 days.'}
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200/80 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'all'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Recommendations ({recommendations.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('strong')}
          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'strong'
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'text-emerald-700 hover:bg-emerald-50'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Strong Matches ({strongMatches.length})</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('alternative')}
          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'alternative'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-indigo-700 hover:bg-indigo-50'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Alternative Career Paths ({alternativePaths.length})</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('exploratory')}
          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'exploratory'
              ? 'bg-amber-600 text-white shadow-sm'
              : 'text-amber-700 hover:bg-amber-50'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Exploratory Tracks ({exploratoryTracks.length})</span>
        </button>
      </div>

      {/* Recommendations Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredRoles.map((role) => {
          const isStrong = role.match_type === 'Strong Match';
          const isAlternative = role.match_type === 'Alternative Career Path';
          return (
            <div
              key={role.role_title}
              className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm flex flex-col justify-between hover:border-indigo-300 transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                      {role.category}
                    </span>
                    <h3 className="text-base font-bold text-slate-900 tracking-tight">
                      {role.role_title}
                    </h3>
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border shrink-0 ${
                      isStrong
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : isAlternative
                        ? 'bg-indigo-50 text-indigo-800 border-indigo-200'
                        : 'bg-amber-50 text-amber-800 border-amber-200'
                    }`}
                  >
                    {role.match_type}
                  </span>
                </div>

                {/* Match Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-600">Core Skill Overlap</span>
                    <strong className="text-slate-900">{role.match_percentage}%</strong>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        isStrong
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-500'
                          : isAlternative
                          ? 'bg-gradient-to-r from-indigo-500 to-violet-500'
                          : 'bg-gradient-to-r from-amber-500 to-orange-500'
                      }`}
                      style={{ width: `${role.match_percentage}%` }}
                    />
                  </div>
                </div>

                {/* Reasoning Box */}
                <p className="text-xs text-slate-600 leading-relaxed p-3.5 rounded-2xl bg-slate-50 border border-slate-100 mb-4">
                  {role.reasoning}
                </p>

                {/* Matched Skills */}
                <div className="space-y-2 mb-3">
                  <span className="text-[11px] font-bold text-emerald-800 flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Your Applicable Skills ({role.matched_skills.length})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {role.matched_skills.length > 0 ? (
                      role.matched_skills.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-0.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200/60 text-[11px] font-medium"
                        >
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">None detected</span>
                    )}
                  </div>
                </div>

                {/* Missing Skills (Skill Gaps) */}
                <div className="space-y-2 mb-3">
                  <span className="text-[11px] font-bold text-rose-800 flex items-center gap-1.5">
                    <Plus className="w-3.5 h-3.5 text-rose-600" />
                    <span>Target Skills to Acquire ({role.missing_skills.length})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {role.missing_skills.length > 0 ? (
                      role.missing_skills.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-0.5 rounded-lg bg-rose-50 text-rose-800 border border-rose-200/60 text-[11px] font-medium"
                        >
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-emerald-600 font-medium">Full Core Coverage!</span>
                    )}
                  </div>
                </div>

                {/* Other Detected Resume Skills (Transferable) */}
                <div className="space-y-2 mb-5">
                  <span className="text-[11px] font-bold text-slate-600 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-slate-500" />
                    <span>Other Detected Resume Skills ({role.transferable_skills?.length || 0})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {role.transferable_skills && role.transferable_skills.length > 0 ? (
                      role.transferable_skills.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-0.5 rounded-lg bg-slate-100 text-slate-700 border border-slate-200/80 text-[11px] font-medium"
                        >
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">None outside core list</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold text-slate-500">
                  Ramp Track: <strong className="text-slate-800">{role.recommended_duration}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => handleSelectRoleForRoadmap(role.role_title)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
                >
                  <span>Build Roadmap</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
