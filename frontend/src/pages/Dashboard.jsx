import React, { useState, useEffect } from 'react';
import { useOutletContext, Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  CheckCircle2,
  TrendingUp,
  UploadCloud,
  Sparkles,
  ArrowRight,
  Clock,
  ShieldCheck,
  ChevronRight,
  Target,
  Layers,
  Award,
  History,
  Bot,
  Compass,
  Zap,
  BarChart3,
  Calendar,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import MetricCard from '../components/MetricCard';
import { useAuth } from '../context/AuthContext';
import { useResume } from '../context/ResumeContext';
import { getHistoryAnalytics, getHistoryList } from '../services/api';

// Custom Tooltip for Recharts
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/95 backdrop-blur-sm p-3 rounded-xl border border-slate-200 shadow-lg text-xs space-y-1">
        <p className="font-bold text-slate-800">{label}</p>
        {payload.map((entry, idx) => (
          <p key={idx} style={{ color: entry.color }} className="font-semibold">
            {entry.name}: {entry.value}{typeof entry.value === 'number' && entry.name.toLowerCase().includes('score') || entry.name.toLowerCase().includes('confidence') ? '%' : ''}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { openUploadModal } = useOutletContext();
  const { user, isAuthenticated } = useAuth();
  const {
    analysisData,
    predictionData,
    matchingData,
    recommendationsData,
    roadmapData,
    suggestionsData,
  } = useResume();

  const [historyAnalytics, setHistoryAnalytics] = useState(null);
  const [historyRecords, setHistoryRecords] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [chartView, setChartView] = useState('skills'); // 'skills' | 'progression'

  // Fetch real user analytics and history records when authenticated
  useEffect(() => {
    let isMounted = true;
    async function loadUserAnalytics() {
      if (!isAuthenticated) return;
      setIsLoadingHistory(true);
      try {
        const [analyticsRes, listRes] = await Promise.all([
          getHistoryAnalytics().catch(() => null),
          getHistoryList().catch(() => ({ records: [] })),
        ]);
        if (isMounted) {
          if (analyticsRes && analyticsRes.success) {
            setHistoryAnalytics(analyticsRes);
          }
          if (listRes && listRes.records) {
            setHistoryRecords(listRes.records);
          }
        }
      } catch (err) {
        console.warn('Dashboard history analytics fetch notice:', err.message);
      } finally {
        if (isMounted) setIsLoadingHistory(false);
      }
    }
    loadUserAnalytics();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, analysisData]);

  const displayName = user?.full_name ? user.full_name.split(' ')[0] : 'Explorer';

  // =========================================================================
  // 1. END-TO-END WORKFLOW STEPPER LOGIC
  // =========================================================================
  const workflowSteps = [
    {
      id: 1,
      title: 'Resume Analysis',
      desc: 'Extracted Skills & Credentials',
      path: '/resume-analysis',
      icon: FileText,
      isComplete: Boolean(analysisData),
      isInProgress: false,
    },
    {
      id: 2,
      title: 'Improvement Suggestions',
      desc: 'Readiness Score & Action Items',
      path: '/resume-analysis',
      icon: Lightbulb,
      isComplete: Boolean(suggestionsData),
      isInProgress: Boolean(analysisData && !suggestionsData),
    },
    {
      id: 3,
      title: 'Domain Fit Prediction',
      desc: 'DistilBERT 24-Class Classifier',
      path: '/job-prediction',
      icon: Briefcase,
      isComplete: Boolean(predictionData),
      isInProgress: Boolean(analysisData && !predictionData),
    },
    {
      id: 4,
      title: 'Semantic Job Match',
      desc: 'Sentence-BERT Cosine Matching',
      path: '/skill-gap',
      icon: Target,
      isComplete: Boolean(matchingData),
      isInProgress: false,
    },
    {
      id: 5,
      title: 'Career Recommendations',
      desc: 'Role Paths & Skill Overlap',
      path: '/recommendations',
      icon: Sparkles,
      isComplete: Boolean(recommendationsData),
      isInProgress: false,
    },
    {
      id: 6,
      title: 'Roadmap & Assistant',
      desc: '30/60-Day Plan & Ollama Chat',
      path: '/roadmap',
      icon: Compass,
      isComplete: Boolean(roadmapData),
      isInProgress: false,
    },
  ];

  const completedStepsCount = workflowSteps.filter((s) => s.isComplete).length;
  const workflowProgressPct = Math.round((completedStepsCount / workflowSteps.length) * 100);

  // =========================================================================
  // 2. REAL METRIC VALUES (Synthesizing active session and user history)
  // =========================================================================
  const activeSkills = analysisData?.skills?.all_skills || [];
  const latestHistSkillsCount = historyAnalytics?.latest_analysis?.skill_count || 0;
  const totalSkillsCount = activeSkills.length > 0 ? activeSkills.length : latestHistSkillsCount;

  const topPrediction = predictionData?.predictions?.[0];
  const histTopRole = historyAnalytics?.latest_analysis?.top_role;
  const histTopConf = historyAnalytics?.latest_analysis?.top_confidence;

  const activeTopRole = topPrediction?.category || histTopRole || 'Pending Analysis';
  const activeTopConfidence = topPrediction
    ? Math.round(topPrediction.confidence * 1000) / 10
    : histTopConf
    ? Math.round(histTopConf * 1000) / 10
    : null;

  const activeReadinessScore =
    suggestionsData?.readiness_score?.overall_score ||
    (historyAnalytics?.score_progression?.slice(-1)[0]?.readiness_score) ||
    null;

  const activeReadinessTier = suggestionsData?.readiness_score?.readiness_tier || (
    activeReadinessScore
      ? activeReadinessScore >= 85
        ? 'Strong Structural Foundation'
        : activeReadinessScore >= 60
        ? 'Moderate Completeness'
        : 'Requires Improvement'
      : 'Structural Completeness'
  );

  const totalSavedAnalyses = historyAnalytics?.total_analyses || historyRecords.length;

  // =========================================================================
  // 3. RECHARTS DATA PREPARATION
  // =========================================================================
  // Skill Category Distribution
  const skillCategoryChartData = [
    {
      name: 'Languages',
      count: analysisData?.skills?.programming_languages?.length || 0,
      fill: '#6366f1',
    },
    {
      name: 'Frameworks',
      count: analysisData?.skills?.frameworks_and_libraries?.length || 0,
      fill: '#8b5cf6',
    },
    {
      name: 'Databases',
      count: analysisData?.skills?.databases?.length || 0,
      fill: '#10b981',
    },
    {
      name: 'Cloud & DevOps',
      count: analysisData?.skills?.cloud_and_devops?.length || 0,
      fill: '#06b6d4',
    },
    {
      name: 'AI & ML',
      count: analysisData?.skills?.ai_and_machine_learning?.length || 0,
      fill: '#d946ef',
    },
  ];

  // If no active resume skills, check if top_skills from history exists
  const hasCategorySkills = skillCategoryChartData.some((d) => d.count > 0);
  const fallbackTopSkillsData = (historyAnalytics?.top_skills || []).slice(0, 5).map((item, idx) => ({
    name: item.skill,
    count: item.count,
    fill: ['#6366f1', '#8b5cf6', '#10b981', '#06b6d4', '#d946ef'][idx % 5],
  }));

  // Progression / Trend Chart Data
  const historicalProgression = historyAnalytics?.score_progression || [];
  const hasHistoryTrend = historicalProgression.length >= 2;

  // Session Multi-Metric Comparison Data (when 1 analysis or active session exists)
  const currentSessionMetrics = [
    {
      metric: 'DistilBERT Conf.',
      score: activeTopConfidence || 0,
      fill: '#6366f1',
    },
    {
      metric: 'Resume Readiness',
      score: activeReadinessScore || 0,
      fill: '#10b981',
    },
    {
      metric: 'JD Skill Coverage',
      score: matchingData?.skill_match?.match_percentage || 0,
      fill: '#8b5cf6',
    },
    {
      metric: 'Semantic Fit',
      score: matchingData?.semantic_match?.similarity_score
        ? Math.round(matchingData.semantic_match.similarity_score * 100)
        : 0,
      fill: '#06b6d4',
    },
  ];

  // =========================================================================
  // 4. DYNAMIC RECENT ACTIVITIES
  // =========================================================================
  const dynamicActivities = [];
  if (analysisData) {
    dynamicActivities.push({
      id: 'active-upload',
      type: 'upload',
      title: `Active resume: "${analysisData.filename}"`,
      detail: `Extracted ${analysisData.skills?.all_skills?.length || 0} skills & ${analysisData.statistics?.experience_count || 0} experience entries`,
      time: 'Current Session',
      icon: FileText,
      iconColor: 'text-indigo-600 bg-indigo-50',
    });
  }
  if (suggestionsData) {
    dynamicActivities.push({
      id: 'active-suggestions',
      type: 'suggestions',
      title: `Resume Readiness Score: ${suggestionsData.readiness_score?.overall_score}/100`,
      detail: `${suggestionsData.summary?.high || 0} high-priority recommendations identified`,
      time: 'Current Session',
      icon: Lightbulb,
      iconColor: 'text-emerald-600 bg-emerald-50',
    });
  }
  if (predictionData) {
    dynamicActivities.push({
      id: 'active-pred',
      type: 'prediction',
      title: `DistilBERT classified domain: ${topPrediction?.category}`,
      detail: `Model confidence: ${Math.round(topPrediction?.confidence * 100)}% across 24 professional categories`,
      time: 'Current Session',
      icon: Briefcase,
      iconColor: 'text-violet-600 bg-violet-50',
    });
  }
  if (matchingData) {
    dynamicActivities.push({
      id: 'active-match',
      type: 'match',
      title: `Sentence-BERT matched against "${matchingData.job_title || 'Target JD'}"`,
      detail: `Semantic similarity: ${Math.round(matchingData.semantic_match?.similarity_score * 100)}% • Keyword match: ${matchingData.skill_match?.match_percentage}%`,
      time: 'Current Session',
      icon: Target,
      iconColor: 'text-cyan-600 bg-cyan-50',
    });
  }
  if (roadmapData?.roadmap) {
    dynamicActivities.push({
      id: 'active-roadmap',
      type: 'roadmap',
      title: `Personalized ${roadmapData.roadmap.duration} learning roadmap generated`,
      detail: `Targeting ${roadmapData.roadmap.role_title} with ${roadmapData.roadmap.milestones?.length || 0} weekly milestones`,
      time: 'Current Session',
      icon: Compass,
      iconColor: 'text-blue-600 bg-blue-50',
    });
  }

  // Fallback to recent history records if active session is sparse
  if (dynamicActivities.length < 3 && historyRecords.length > 0) {
    historyRecords.slice(0, 3 - dynamicActivities.length).forEach((rec) => {
      dynamicActivities.push({
        id: rec.id,
        type: 'history',
        title: `Historical Analysis: "${rec.filename}"`,
        detail: `Identified ${rec.skill_count} skills • Top Role: ${rec.top_role || 'General'}`,
        time: rec.created_at ? rec.created_at.slice(0, 10) : 'Past Session',
        icon: History,
        iconColor: 'text-slate-600 bg-slate-100',
      });
    });
  }

  const hasAnyData = Boolean(analysisData || historyRecords.length > 0);

  return (
    <div className="space-y-8 animate-fadeIn pb-8">
      {/* 1. Welcome Banner & Hero Actions */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 rounded-3xl p-6 sm:p-8 text-white shadow-xl">
        <div className="absolute -right-16 -top-16 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-1/3 -bottom-20 w-60 h-60 bg-violet-500/15 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-indigo-200 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Career Intelligence Active</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-2">
              Welcome back, {displayName}! 👋
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              {analysisData ? (
                <>
                  Active session for candidate <strong className="text-white font-semibold">{analysisData.filename}</strong>.
                  Identified <strong className="text-white font-semibold">{totalSkillsCount} skills</strong> with primary alignment in <strong className="text-white font-semibold">{activeTopRole}</strong>.
                </>
              ) : historyRecords.length > 0 ? (
                <>
                  You have <strong className="text-white font-semibold">{totalSavedAnalyses} saved analysis record(s)</strong> in your evaluation history.
                  Latest profile identified <strong className="text-white font-semibold">{totalSkillsCount} skills</strong> aligned with <strong className="text-white font-semibold">{activeTopRole}</strong>.
                </>
              ) : (
                <>
                  Your privacy-first career copilot is ready. Upload a resume to predict job roles with fine-tuned DistilBERT, measure semantic match with Sentence-BERT, and generate structured learning roadmaps.
                </>
              )}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={openUploadModal}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white text-slate-900 hover:bg-slate-100 text-xs font-bold shadow-lg transition-all active:scale-95 cursor-pointer"
            >
              <UploadCloud className="w-4 h-4 text-indigo-600" />
              <span>Upload New Resume</span>
            </button>
            <Link
              to="/history"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/20 text-white text-xs font-semibold backdrop-blur-sm transition-all"
            >
              <History className="w-3.5 h-3.5 text-indigo-300" />
              <span>Evaluation History</span>
            </Link>
          </div>
        </div>

        {/* Live Status Indicator Bar */}
        <div className="relative z-10 mt-6 pt-4 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>
              {hasAnyData
                ? 'Live Workspace Active • All metrics computed from real candidate evaluations'
                : 'Awaiting Document Upload • Ready for in-memory analysis'}
            </span>
          </span>
          <span className="text-slate-400">Zero Cloud Leakage • Local AI • Strictly Private</span>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* 2. END-TO-END CAREERAI WORKFLOW STEPPER                              */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" />
              <span>End-to-End CareerAI Workflow Progress</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Track your progression through the 6 core stages of candidate analysis and career planning.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-indigo-600">
              {completedStepsCount} of {workflowSteps.length} Stages Completed
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              {workflowProgressPct}%
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-6">
          <div
            className="h-full bg-gradient-to-r from-indigo-600 to-violet-600 rounded-full transition-all duration-500"
            style={{ width: `${workflowProgressPct}%` }}
          />
        </div>

        {/* 6 Interactive Stage Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {workflowSteps.map((step) => {
            const Icon = step.icon;
            const isClickable = Boolean(analysisData || step.id === 1);

            return (
              <button
                key={step.id}
                type="button"
                onClick={() => isClickable && navigate(step.path)}
                disabled={!isClickable}
                className={`p-3.5 rounded-2xl border text-left transition-all flex flex-col justify-between h-full ${
                  step.isComplete
                    ? 'bg-emerald-50/50 border-emerald-200/80 hover:bg-emerald-50'
                    : step.isInProgress
                    ? 'bg-amber-50/50 border-amber-200/80 hover:bg-amber-50'
                    : isClickable
                    ? 'bg-slate-50 border-slate-200/70 hover:bg-slate-100/80'
                    : 'bg-slate-50/50 border-slate-100 opacity-60 cursor-not-allowed'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`p-1.5 rounded-xl ${
                        step.isComplete
                          ? 'bg-emerald-100 text-emerald-700'
                          : step.isInProgress
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-200/80 text-slate-600'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    {step.isComplete ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    ) : step.isInProgress ? (
                      <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    ) : (
                      <span className="text-[10px] font-bold text-slate-400">#{step.id}</span>
                    )}
                  </div>

                  <h4 className="text-xs font-bold text-slate-900 leading-snug line-clamp-1">
                    {step.title}
                  </h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-2">
                    {step.desc}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-200/40 flex items-center justify-between text-[10px] font-semibold">
                  <span
                    className={
                      step.isComplete
                        ? 'text-emerald-700 font-bold'
                        : step.isInProgress
                        ? 'text-amber-700 font-bold'
                        : 'text-slate-400'
                    }
                  >
                    {step.isComplete ? 'Complete' : step.isInProgress ? 'Ready' : 'Pending'}
                  </span>
                  {isClickable && <ArrowRight className="w-3 h-3 text-slate-400" />}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ===================================================================== */}
      {/* 3. REAL KEY METRICS GRID (4 Summary Cards)                           */}
      {/* ===================================================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Skills Identified"
          value={totalSkillsCount > 0 ? `${totalSkillsCount} Verified` : '0 Skills'}
          subtitle={
            analysisData
              ? `Extracted across ${analysisData.skills?.programming_languages?.length || 0} languages and ${analysisData.skills?.frameworks_and_libraries?.length || 0} frameworks.`
              : 'Upload a resume to extract technical taxonomy.'
          }
          icon={CheckCircle2}
          trend={totalSkillsCount > 0 ? 'Verified In-Memory' : 'Awaiting Resume'}
          trendPositive={totalSkillsCount > 0}
          accentColor="indigo"
          progress={Math.min(100, totalSkillsCount * 4)}
        />

        <MetricCard
          title="Top Predicted Role"
          value={activeTopConfidence !== null ? `${activeTopConfidence}% Conf.` : 'Pending'}
          subtitle={
            activeTopConfidence !== null
              ? `${activeTopRole} • Model softmax confidence (not hiring probability).`
              : 'Run DistilBERT classifier to evaluate domain fit.'
          }
          icon={Briefcase}
          trend={activeTopConfidence !== null ? 'DistilBERT 24-Class' : 'Pending'}
          trendPositive={activeTopConfidence !== null && activeTopConfidence >= 40}
          accentColor="violet"
          progress={activeTopConfidence || 0}
        />

        <MetricCard
          title="Resume Readiness"
          value={activeReadinessScore !== null ? `${activeReadinessScore} / 100` : 'Pending'}
          subtitle={
            activeReadinessScore !== null
              ? `${activeReadinessTier} • Structural completeness heuristic.`
              : 'Evaluate resume structure, action verbs, and metrics.'
          }
          icon={Award}
          trend={
            activeReadinessScore !== null
              ? activeReadinessScore >= 85
                ? 'Strong Base'
                : 'Action Items'
              : 'Pending'
          }
          trendPositive={activeReadinessScore !== null && activeReadinessScore >= 60}
          accentColor="emerald"
          progress={activeReadinessScore || 0}
        />

        <MetricCard
          title="Saved Evaluations"
          value={totalSavedAnalyses > 0 ? `${totalSavedAnalyses} Record(s)` : 'Session Only'}
          subtitle={
            isAuthenticated
              ? `Persistent history active for ${user?.email || 'authenticated user'}.`
              : 'Guest mode active • Register to sync history permanently.'
          }
          icon={History}
          trend={isAuthenticated ? 'Account Synced' : 'Guest Mode'}
          trendPositive={isAuthenticated}
          accentColor="blue"
          progress={Math.min(100, totalSavedAnalyses * 25)}
        />
      </div>

      {/* ===================================================================== */}
      {/* 4. REAL RECHARTS VISUALIZATION SECTION                                */}
      {/* ===================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart Column (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-600" />
                  <span>
                    {chartView === 'skills'
                      ? 'Technical Skill Category Distribution'
                      : 'Evaluation Score & Historical Progression'}
                  </span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {chartView === 'skills'
                    ? 'Breakdown of extracted technical competencies across primary software disciplines.'
                    : 'Track your candidate confidence, readiness score, and semantic coverage over time.'}
                </p>
              </div>

              {/* Chart Switcher Buttons */}
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 self-start sm:self-auto">
                <button
                  type="button"
                  onClick={() => setChartView('skills')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    chartView === 'skills'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Skill Categories
                </button>
                <button
                  type="button"
                  onClick={() => setChartView('progression')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    chartView === 'progression'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Score Progression
                </button>
              </div>
            </div>

            {/* Chart Canvas */}
            <div className="h-64 sm:h-72 w-full">
              {chartView === 'skills' ? (
                hasCategorySkills || fallbackTopSkillsData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={hasCategorySkills ? skillCategoryChartData : fallbackTopSkillsData}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="count" name="Identified Skills" radius={[8, 8, 0, 0]}>
                        {(hasCategorySkills ? skillCategoryChartData : fallbackTopSkillsData).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                    <FileText className="w-8 h-8 text-slate-400 mb-2" />
                    <p className="text-xs font-bold text-slate-700">No skills identified yet</p>
                    <p className="text-[11px] text-slate-500 max-w-xs mt-0.5">
                      Upload your resume to automatically categorize your technical stack.
                    </p>
                    <button
                      type="button"
                      onClick={openUploadModal}
                      className="mt-3 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold cursor-pointer"
                    >
                      Upload Resume
                    </button>
                  </div>
                )
              ) : (
                /* Progression View */
                hasHistoryTrend ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={historicalProgression}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="colorConf" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                        </linearGradient>
                        <linearGradient id="colorReady" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="top_confidence"
                        name="Model Confidence (%)"
                        stroke="#6366f1"
                        strokeWidth={2.5}
                        fillOpacity={1}
                        fill="url(#colorConf)"
                      />
                      <Area
                        type="monotone"
                        dataKey="readiness_score"
                        name="Readiness Score"
                        stroke="#10b981"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorReady)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : currentSessionMetrics.some((m) => m.score > 0) ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={currentSessionMetrics}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="score" name="Score (%)" radius={[8, 8, 0, 0]}>
                        {currentSessionMetrics.map((entry, index) => (
                          <Cell key={`mcell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                    <History className="w-8 h-8 text-slate-400 mb-2" />
                    <p className="text-xs font-bold text-slate-700">No score progression data</p>
                    <p className="text-[11px] text-slate-500 max-w-xs mt-0.5">
                      Save multiple resume evaluations or run predictions to track your confidence and readiness trends.
                    </p>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Chart Sub-Footer */}
          <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>Deterministic Keyword & ML Transformer Analytics</span>
            <span>Zero Hallucinated Metrics</span>
          </div>
        </div>

        {/* Recent Analysis Activity Stream (1 Col) */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-600" />
                <span>Recent Analysis Events</span>
              </h3>
              <Link
                to="/history"
                className="text-[11px] font-bold text-indigo-600 hover:text-indigo-700"
              >
                View All
              </Link>
            </div>

            {dynamicActivities.length > 0 ? (
              <div className="space-y-4">
                {dynamicActivities.map((act) => {
                  const Icon = act.icon;
                  return (
                    <div key={act.id} className="flex items-start gap-3">
                      <div className={`p-2 rounded-xl shrink-0 ${act.iconColor}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline justify-between gap-1">
                          <h4 className="text-xs font-bold text-slate-900 truncate">
                            {act.title}
                          </h4>
                          <span className="text-[10px] text-slate-400 shrink-0">
                            {act.time}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2 leading-relaxed">
                          {act.detail}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 space-y-2">
                <Clock className="w-6 h-6 mx-auto text-slate-300" />
                <p className="text-xs font-medium">No recent activity detected.</p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                  Upload a resume or explore career recommendations to generate live audit logs.
                </p>
              </div>
            )}
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100">
            <Link
              to="/history"
              className="w-full inline-flex items-center justify-center gap-1.5 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold transition-colors"
            >
              <span>Manage Evaluation History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* 5. CAREER RECOMMENDATIONS / ACTION ROADMAP PREVIEW                   */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-6 mb-6 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" />
              <span>Recommended Career Trajectories</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Role fits computed from your verified skills taxonomy and DistilBERT domain predictions.
            </p>
          </div>
          <Link
            to="/recommendations"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100/80 text-indigo-700 text-xs font-bold transition-colors self-start sm:self-auto"
          >
            <span>Explore All 24 Roles</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recommendationsData?.strong_matches && recommendationsData.strong_matches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {recommendationsData.strong_matches.slice(0, 3).map((rec, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-slate-50 border border-slate-200/70 flex flex-col justify-between hover:border-indigo-300 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                      Strong Match
                    </span>
                    <span className="text-xs font-bold text-slate-900">
                      {rec.overlap_percentage}% Skill Overlap
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 mb-1">
                    {rec.role_title}
                  </h4>
                  <p className="text-xs text-slate-500 line-clamp-2 mb-3">
                    {rec.fit_rationale}
                  </p>

                  <div className="space-y-1.5 pt-2 border-t border-slate-200/50">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Core Skills:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {rec.core_skills.slice(0, 4).map((s, sIdx) => (
                        <span
                          key={sIdx}
                          className="text-[10px] px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 font-medium"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-200/60 flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-500">
                    Missing: {rec.missing_skills.length} skills
                  </span>
                  <Link
                    to="/roadmap"
                    className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-700"
                  >
                    <span>View Roadmap</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Generate Explainable Career Role Recommendations
              </h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xl">
                Compare your extracted resume skills against benchmark software roles, identify exact missing competencies, and generate personalized 30/60-day roadmaps.
              </p>
            </div>
            <Link
              to="/recommendations"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 hover:from-indigo-500 hover:to-violet-500 transition-all shrink-0 cursor-pointer"
            >
              Run Recommendations
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
