import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Mail,
  Phone,
  GraduationCap,
  Briefcase,
  Code2,
  Terminal,
  Database,
  Cloud,
  Cpu,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileCode,
  Sparkles,
  ArrowRight,
  Target,
  TrendingUp,
  ShieldCheck,
  Lightbulb,
  Check,
  Sliders,
  Award,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';
import { getAvailableRoles } from '../services/api';

export default function ResumeAnalysis() {
  const navigate = useNavigate();
  const {
    analysisData,
    isLoading,
    error,
    uploadFile,
    clearAnalysis,
    suggestionsData,
    isLoadingSuggestions,
    suggestionsError,
    fetchResumeSuggestions,
    selectedTargetRole,
    setSelectedTargetRole,
  } = useResume();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [localError, setLocalError] = useState(null);
  const [showTextPreview, setShowTextPreview] = useState(false);

  // Tab and Suggestions View State
  const [activeTab, setActiveTab] = useState('suggestions'); // 'suggestions' | 'overview'
  const [priorityFilter, setPriorityFilter] = useState('ALL'); // 'ALL' | 'High' | 'Medium' | 'Low'
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [expandedExamples, setExpandedExamples] = useState({});
  const [targetRoleSelection, setTargetRoleSelection] = useState(selectedTargetRole || '');
  const [availableRolesList, setAvailableRolesList] = useState([]);

  // Fetch benchmark roles on mount for targeting dropdown
  useEffect(() => {
    let isMounted = true;
    async function loadRoles() {
      try {
        const roles = await getAvailableRoles();
        if (isMounted && Array.isArray(roles) && roles.length > 0) {
          setAvailableRolesList(roles);
        }
      } catch (err) {
        // Fallback default benchmark roles
        if (isMounted) {
          setAvailableRolesList([
            'Full Stack Software Engineer',
            'Backend Software Engineer',
            'Frontend Software Engineer',
            'Data Scientist & ML Practitioner',
            'Cloud & DevOps Engineer',
            'Database Administrator & Data Engineer',
          ]);
        }
      }
    }
    loadRoles();
    return () => {
      isMounted = false;
    };
  }, []);

  // Automatically trigger suggestions analysis when resume is parsed if not yet fetched
  useEffect(() => {
    if (analysisData && !suggestionsData && !isLoadingSuggestions) {
      fetchResumeSuggestions(selectedTargetRole || null);
    }
  }, [analysisData, suggestionsData, isLoadingSuggestions, selectedTargetRole, fetchResumeSuggestions]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setLocalError(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcess(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    setLocalError(null);
    if (e.target.files && e.target.files[0]) {
      validateAndProcess(e.target.files[0]);
    }
  };

  const validateAndProcess = async (file) => {
    const lower = file.name.toLowerCase();
    if (!lower.endsWith('.pdf') && !lower.endsWith('.docx')) {
      setLocalError('Unsupported format. Please select a PDF (.pdf) or Word document (.docx).');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setLocalError('File size exceeds the 5 MB limit.');
      return;
    }
    setSelectedFile(file);
    try {
      await uploadFile(file);
    } catch (err) {
      setLocalError(err.message || 'Failed to analyze resume.');
    }
  };

  const handleTargetRoleEvaluate = async (roleToUse) => {
    setSelectedTargetRole(roleToUse || null);
    setTargetRoleSelection(roleToUse || '');
    try {
      await fetchResumeSuggestions(roleToUse || null, [], true);
    } catch (err) {
      console.warn('Target role evaluation notice:', err.message);
    }
  };

  const toggleExampleExpand = (suggId) => {
    setExpandedExamples((prev) => ({
      ...prev,
      [suggId]: !prev[suggId],
    }));
  };

  // 1. If No Resume Uploaded Yet: Render In-Page Upload Dropzone
  if (!analysisData && !isLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto animate-fadeIn">
        {/* Module Introduction Card */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Resume Analysis & Improvement Engine
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Upload your resume in PDF or DOCX format for instant in-memory text parsing, structural readiness scoring, quantifiable impact checks, and prioritized improvement suggestions.
              </p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {(error || localError) && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <div>
              <p className="font-semibold">Analysis Failed</p>
              <p className="text-rose-600 mt-0.5">{error || localError}</p>
            </div>
          </div>
        )}

        {/* Drag and Drop Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-3xl p-12 text-center flex flex-col items-center justify-center transition-all bg-white shadow-sm ${
            dragActive
              ? 'border-indigo-500 bg-indigo-50/40 scale-[0.99]'
              : 'border-slate-200 hover:border-indigo-300'
          }`}
        >
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border border-indigo-100">
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-base font-bold text-slate-900 mb-1">
            Upload your resume document
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mb-6 leading-relaxed">
            Drag and drop your file here, or click to browse from your computer. Supports PDF and Word documents up to 5 MB.
          </p>

          <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-sm shadow-indigo-500/20 active:scale-95 cursor-pointer transition-all">
            <FileText className="w-4 h-4" />
            <span>Select PDF or DOCX File</span>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          <div className="mt-8 pt-6 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Note: Uploaded resume content and extracted skills are stored securely for career analysis and platform administration.</span>
          </div>
        </div>
      </div>
    );
  }

  // 2. Loading State: Document Being Analyzed
  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center animate-fadeIn">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-6 shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">
          Analyzing Document...
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          Extracting text blocks with PyMuPDF, identifying technical skills, educational credentials, and employment records.
        </p>
      </div>
    );
  }

  // 3. Results View: Real Backend Response
  const {
    filename,
    file_type,
    contact_info,
    skills,
    education,
    experience,
    projects = [],
    statistics,
    text_preview,
  } = analysisData;

  const skillCategories = [
    {
      title: 'Programming Languages',
      items: skills.programming_languages || [],
      icon: Code2,
      color: 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
    },
    {
      title: 'Frameworks & Libraries',
      items: skills.frameworks_and_libraries || [],
      icon: Terminal,
      color: 'bg-violet-50 text-violet-700 border-violet-200/60',
    },
    {
      title: 'Databases',
      items: skills.databases || [],
      icon: Database,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    },
    {
      title: 'Cloud & DevOps / Tools',
      items: skills.cloud_and_devops || [],
      icon: Cloud,
      color: 'bg-blue-50 text-blue-700 border-blue-200/60',
    },
    {
      title: 'AI & Machine Learning',
      items: skills.ai_and_machine_learning || [],
      icon: Cpu,
      color: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200/60',
    },
  ];

  // Suggestions Filtering Logic
  const allSuggestions = suggestionsData?.suggestions || [];
  const readiness = suggestionsData?.readiness_score;

  const filteredSuggestions = allSuggestions.filter((item) => {
    if (priorityFilter !== 'ALL' && item.priority !== priorityFilter) return false;
    if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;
    return true;
  });

  const uniqueCategories = Array.from(new Set(allSuggestions.map((s) => s.category)));

  // Readiness Tier Styling
  const getReadinessBadge = (score, tier) => {
    if (score >= 85) {
      return {
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
        ring: 'text-emerald-600',
        label: tier || 'Strong Structural Foundation',
      };
    }
    if (score >= 60) {
      return {
        bg: 'bg-amber-50 text-amber-700 border-amber-200/80',
        ring: 'text-amber-600',
        label: tier || 'Moderate Completeness',
      };
    }
    return {
      bg: 'bg-rose-50 text-rose-700 border-rose-200/80',
      ring: 'text-rose-600',
      label: tier || 'Requires Significant Improvement',
    };
  };

  const badgeProps = readiness
    ? getReadinessBadge(readiness.overall_score, readiness.readiness_tier)
    : { bg: 'bg-slate-50 text-slate-700 border-slate-200', ring: 'text-slate-500', label: 'Analyzing...' };

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fadeIn">
      {/* Top Document Summary Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <h2 className="text-lg font-bold text-slate-900 truncate max-w-md">
                  {filename}
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  {file_type}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Verified analysis generated from backend parsing engine
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={clearAnalysis}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Analyze Another Resume</span>
          </button>
        </div>

        {/* Structural Statistics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Technical Skills
            </span>
            <p className="text-xl font-bold text-slate-900 mt-1">
              {statistics.skill_count}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">Verified in taxonomy</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Experience Entries
            </span>
            <p className="text-xl font-bold text-slate-900 mt-1">
              {statistics.experience_count}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {experience.total_years_estimated
                ? `${experience.total_years_estimated} yrs estimated`
                : 'Employment records'}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Education Entries
            </span>
            <p className="text-xl font-bold text-slate-900 mt-1">
              {statistics.education_count}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">Degrees & qualifications</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Word Count
            </span>
            <p className="text-xl font-bold text-slate-900 mt-1">
              {statistics.word_count}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">{statistics.character_count} chars</p>
          </div>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200/80 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('suggestions')}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'suggestions'
              ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-500/20'
              : 'bg-white text-slate-700 border border-slate-200/80 hover:bg-slate-50'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Improvement Suggestions & Readiness</span>
          {readiness && (
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              activeTab === 'suggestions' ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-700'
            }`}>
              {readiness.overall_score}/100
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'overview'
              ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-500/20'
              : 'bg-white text-slate-700 border border-slate-200/80 hover:bg-slate-50'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Parsed Resume Sections & Overview</span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            activeTab === 'overview' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
          }`}>
            {statistics.skill_count} Skills
          </span>
        </button>
      </div>

      {/* =================================================================== */}
      {/* TAB 1: IMPROVEMENT SUGGESTIONS & STRUCTURAL READINESS SCORE         */}
      {/* =================================================================== */}
      {activeTab === 'suggestions' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Target Role Selector Toolbar */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-violet-50 text-violet-600">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Target Career Role Evaluation
                </h3>
                <p className="text-xs text-slate-500">
                  Tailor skill gap recommendations and keyword alignment against a specific role.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
              <select
                value={targetRoleSelection}
                onChange={(e) => handleTargetRoleEvaluate(e.target.value)}
                className="px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer min-w-[220px]"
              >
                <option value="">General Comprehensive Audit</option>
                {availableRolesList.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={() => handleTargetRoleEvaluate(targetRoleSelection)}
                disabled={isLoadingSuggestions}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-all shadow-sm active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                {isLoadingSuggestions ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                <span>Re-Evaluate</span>
              </button>
            </div>
          </div>

          {/* Loading Suggestions State */}
          {isLoadingSuggestions && !suggestionsData && (
            <div className="py-12 text-center bg-white rounded-3xl border border-slate-200/80 p-8">
              <Loader2 className="w-7 h-7 animate-spin text-indigo-600 mx-auto mb-3" />
              <p className="text-sm font-bold text-slate-900">
                Evaluating Resume Structure & Impact...
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Checking action-verb phrasing, quantifiable metrics, section balance, and ATS keywords.
              </p>
            </div>
          )}

          {/* Suggestions Error Banner */}
          {suggestionsError && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <div>
                <p className="font-semibold">Suggestions Evaluation Notice</p>
                <p className="text-rose-600 mt-0.5">{suggestionsError}</p>
              </div>
            </div>
          )}

          {/* Readiness Score Breakdown Card */}
          {readiness && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pb-8 border-b border-slate-100">
                {/* Score Dial / Big Number */}
                <div className="lg:col-span-4 flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-50 border border-slate-100 text-center">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Structural Completeness Score
                  </span>
                  <div className="flex items-baseline gap-1 my-1">
                    <span className="text-5xl font-black text-slate-900 tracking-tight">
                      {readiness.overall_score}
                    </span>
                    <span className="text-xl font-bold text-slate-400">/ 100</span>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border mt-3 ${badgeProps.bg}`}>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{badgeProps.label}</span>
                  </span>
                </div>

                {/* Categories Progress Bars */}
                <div className="lg:col-span-8 space-y-3.5">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Category Completeness Breakdown
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      Heuristic Evaluation
                    </span>
                  </div>

                  {readiness.category_scores?.map((cat) => (
                    <div key={cat.category} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800">{cat.category}</span>
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            cat.status === 'Complete'
                              ? 'bg-emerald-50 text-emerald-700'
                              : cat.status === 'Needs Improvement'
                              ? 'bg-amber-50 text-amber-700'
                              : 'bg-rose-50 text-rose-700'
                          }`}>
                            {cat.status}
                          </span>
                          <span className="font-bold text-slate-700">
                            {cat.score} / {cat.max_score} pts
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            cat.percentage >= 80
                              ? 'bg-emerald-500'
                              : cat.percentage >= 50
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${cat.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ethical Disclaimer Box */}
              <div className="mt-6 p-4 rounded-2xl bg-slate-50 border border-slate-200/60 flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  <strong className="text-slate-700">Structural Completeness Notice: </strong>
                  {readiness.disclaimer}
                </p>
              </div>
            </div>
          )}

          {/* Suggestions Filters & Counter */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Prioritized Action Items ({filteredSuggestions.length})
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Targeted recommendations ordered by urgency and expected recruiter impact.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Priority Filters */}
              {['ALL', 'High', 'Medium', 'Low'].map((p) => {
                const count = p === 'ALL'
                  ? allSuggestions.length
                  : allSuggestions.filter((s) => s.priority === p).length;
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriorityFilter(p)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                      priorityFilter === p
                        ? p === 'High'
                          ? 'bg-rose-600 text-white'
                          : p === 'Medium'
                          ? 'bg-amber-600 text-white'
                          : p === 'Low'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-900 text-white'
                        : 'bg-white text-slate-600 border border-slate-200/80 hover:bg-slate-50'
                    }`}
                  >
                    {p === 'ALL' ? 'All' : p} ({count})
                  </button>
                );
              })}

              {/* Category Filter Dropdown */}
              {uniqueCategories.length > 1 && (
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
                >
                  <option value="ALL">All Categories</option>
                  {uniqueCategories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {/* Suggestions Cards List */}
          {filteredSuggestions.length > 0 ? (
            <div className="space-y-4">
              {filteredSuggestions.map((item) => {
                const isExpanded = Boolean(expandedExamples[item.id]);
                const priorityBadge =
                  item.priority === 'High'
                    ? 'bg-rose-50 text-rose-700 border-rose-200/80'
                    : item.priority === 'Medium'
                    ? 'bg-amber-50 text-amber-700 border-amber-200/80'
                    : 'bg-blue-50 text-blue-700 border-blue-200/80';

                return (
                  <div
                    key={item.id}
                    className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm hover:border-slate-300 transition-all"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${priorityBadge}`}>
                          {item.priority} Priority
                        </span>
                        <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
                          {item.category}
                        </span>
                        <span className="text-[10px] font-medium text-slate-400 capitalize">
                          Action: {item.action_type}
                        </span>
                      </div>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 mb-1.5">
                      {item.title}
                    </h4>

                    {/* Detected Issue */}
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-xs text-slate-600 mb-3">
                      <p className="font-semibold text-slate-700 mb-0.5">Detected Issue:</p>
                      <p>{item.issue}</p>
                    </div>

                    {/* Actionable Recommendation */}
                    <div className="p-3.5 rounded-2xl bg-indigo-50/50 border border-indigo-100/70 text-xs text-indigo-950 mb-3">
                      <p className="font-semibold text-indigo-900 mb-0.5 flex items-center gap-1.5">
                        <Lightbulb className="w-3.5 h-3.5 text-indigo-600" />
                        <span>How to Fix It:</span>
                      </p>
                      <p className="leading-relaxed">{item.recommendation}</p>
                    </div>

                    {/* Expandable Before/After Rewrite Examples */}
                    {item.examples && item.examples.length > 0 && (
                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={() => toggleExampleExpand(item.id)}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors cursor-pointer"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>
                            {isExpanded
                              ? 'Hide High-Impact Rewrite Templates'
                              : `View High-Impact Rewrite Templates (${item.examples.length})`}
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>

                        {isExpanded && (
                          <div className="space-y-3 mt-3 pt-3 border-t border-slate-100">
                            {item.examples.map((ex, idx) => (
                              <div
                                key={idx}
                                className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70 space-y-2.5"
                              >
                                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                                  Template {idx + 1}: {ex.context}
                                </span>

                                <div className="space-y-1.5 text-xs">
                                  <div className="p-2.5 rounded-xl bg-rose-50/80 border border-rose-200/70 text-rose-900">
                                    <span className="font-bold block text-[10px] uppercase tracking-wider text-rose-600 mb-0.5">
                                      Before (Passive / Unquantified):
                                    </span>
                                    <p className="italic">"{ex.before}"</p>
                                  </div>

                                  <div className="p-2.5 rounded-xl bg-emerald-50/80 border border-emerald-200/70 text-emerald-950">
                                    <span className="font-bold block text-[10px] uppercase tracking-wider text-emerald-600 mb-0.5">
                                      After (Metric-Driven XYZ Formula):
                                    </span>
                                    <p className="font-medium">"{ex.after}"</p>
                                  </div>

                                  <p className="text-[11px] text-slate-500 leading-relaxed pt-1">
                                    <strong className="text-slate-700">Why this works: </strong>
                                    {ex.explanation}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-8 text-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-900">No matching suggestions</h4>
              <p className="text-xs text-slate-500 mt-1">
                All checks in this priority tier or category are satisfied.
              </p>
            </div>
          )}

          {/* Bottom Next Step Callout */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Ready to evaluate role fit?
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Compare your resume against 24 career domains with DistilBERT, or match against a custom job description with Sentence-BERT.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => navigate('/skill-gap')}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold transition-all cursor-pointer"
              >
                Match Job Description
              </button>
              <button
                type="button"
                onClick={() => navigate('/job-prediction')}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
              >
                <span>Continue to Job Prediction</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: PARSED RESUME SECTIONS & OVERVIEW                            */}
      {/* =================================================================== */}
      {activeTab === 'overview' && (
        <div className="space-y-6 animate-fadeIn">
          {/* AI Job Role Prediction Callout Banner */}
          <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-violet-900 rounded-3xl p-6 sm:p-7 text-white shadow-md shadow-indigo-950/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
            <div className="flex items-start sm:items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-white shrink-0 shadow-inner">
                <Sparkles className="w-6 h-6 text-indigo-300" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/20 text-indigo-100 border border-white/20">
                    Phase 9 Live Feature
                  </span>
                  <h3 className="text-base font-bold text-white tracking-tight">
                    Predict Job Roles with DistilBERT
                  </h3>
                </div>
                <p className="text-xs text-indigo-100/80 leading-relaxed max-w-xl">
                  Run bidirectional self-attention on your parsed resume content across 24 professional career categories. No re-upload required.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => navigate('/job-prediction')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-indigo-900 text-xs font-bold shadow-sm active:scale-95 transition-all shrink-0 cursor-pointer"
            >
              <span>Predict Job Roles</span>
              <ArrowRight className="w-4 h-4 text-indigo-600" />
            </button>
          </div>

          {/* Contact Information & Overview */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">
              Contact Information
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                  <Mail className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold text-slate-400">Email Address</p>
                  <p className="text-xs font-semibold text-slate-800 truncate mt-0.5">
                    {contact_info?.email || 'Not provided in document'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                  <Phone className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold text-slate-400">Phone Number</p>
                  <p className="text-xs font-semibold text-slate-800 truncate mt-0.5">
                    {contact_info?.phone || 'Not provided in document'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Extracted Technical Skills (Categorized) */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  Extracted Technical Skills
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Extracted via exact multi-word regex boundary matching across verified taxonomy
                </p>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                {statistics.skill_count} Total Identified
              </span>
            </div>

            <div className="space-y-6">
              {skillCategories.map((cat, idx) => (
                <div key={idx} className="space-y-2.5">
                  <div className="flex items-center gap-2">
                    <cat.icon className="w-3.5 h-3.5 text-slate-400" />
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      {cat.title} ({cat.items.length})
                    </h4>
                  </div>
                  {cat.items.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {cat.items.map((skill, sIdx) => (
                        <span
                          key={sIdx}
                          className={`text-xs font-semibold px-3 py-1 rounded-xl border ${cat.color}`}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">None detected in this category.</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Educational Qualifications */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-2.5 mb-6">
              <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                <GraduationCap className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Educational Credentials & Qualifications
              </h3>
            </div>

            {education && education.length > 0 ? (
              <div className="space-y-4">
                {education.map((edu, idx) => (
                  <div key={idx} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <h4 className="text-sm font-bold text-slate-900">{edu.degree}</h4>
                      {edu.year && (
                        <span className="text-[11px] font-medium text-slate-400">{edu.year}</span>
                      )}
                    </div>
                    {edu.institution && (
                      <p className="text-xs font-semibold text-indigo-600 mb-1">
                        {edu.institution}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-2">
                      {edu.field_of_study && <span>Major: {edu.field_of_study}</span>}
                      {edu.score && (
                        <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 font-medium border border-emerald-200/60">
                          Score: {edu.score}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No formal education entries detected.</p>
            )}
          </div>

          {/* Academic & Personal Projects */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-violet-50 text-violet-600">
                  <Code2 className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  Academic, Personal & Capstone Projects
                </h3>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-violet-50 text-violet-700 border border-violet-200/60">
                {projects.length} Identified
              </span>
            </div>

            {projects && projects.length > 0 ? (
              <div className="space-y-4">
                {projects.map((proj, idx) => (
                  <div key={idx} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                    <h4 className="text-sm font-bold text-slate-900 mb-1">{proj.title}</h4>
                    {proj.description && (
                      <p className="text-xs text-slate-600 leading-relaxed mb-3">
                        {proj.description}
                      </p>
                    )}
                    {proj.technologies && proj.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {proj.technologies.map((t, tIdx) => (
                          <span
                            key={tIdx}
                            className="text-[10px] font-semibold px-2.5 py-0.5 rounded-lg bg-white border border-slate-200 text-slate-700"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No project entries detected.</p>
            )}
          </div>

          {/* Professional Employment Experience */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                  <Briefcase className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  Professional Employment Experience
                </h3>
              </div>
              {experience.total_years_estimated && (
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                  {experience.total_years_estimated} Years Total
                </span>
              )}
            </div>

            {experience.entries && experience.entries.length > 0 ? (
              <div className="space-y-4">
                {experience.entries.map((entry, idx) => (
                  <div key={idx} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <h4 className="text-sm font-bold text-slate-900">{entry.title || 'Role'}</h4>
                      {entry.duration && (
                        <span className="text-[11px] font-medium text-slate-400">
                          {entry.duration}
                        </span>
                      )}
                    </div>
                    {entry.organization && (
                      <p className="text-xs font-semibold text-indigo-600 mb-2">
                        {entry.organization}
                      </p>
                    )}
                    <p className="text-xs text-slate-600 leading-relaxed">{entry.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                No professional employment entries detected.
              </p>
            )}
          </div>

          {/* Document Text Preview Collapsible */}
          <div className="bg-white rounded-3xl border border-slate-200/80 overflow-hidden shadow-sm">
            <button
              type="button"
              onClick={() => setShowTextPreview(!showTextPreview)}
              className="w-full flex items-center justify-between p-6 hover:bg-slate-50 transition-colors text-left cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <FileCode className="w-4 h-4 text-slate-500" />
                <span className="text-sm font-bold text-slate-900">Extracted Document Text Preview</span>
              </div>
              {showTextPreview ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {showTextPreview && (
              <div className="p-6 pt-0 border-t border-slate-100">
                <pre className="p-4 rounded-2xl bg-slate-50 text-[11px] text-slate-700 font-mono whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto border border-slate-200/60">
                  {text_preview}
                </pre>
              </div>
            )}
          </div>

          {/* Next Step Action Card */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Next: Match Your Resume Against 24 Career Domains
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Our fine-tuned DistilBERT transformer uses the parsed resume text to compute domain-level fit.
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/job-prediction')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all shrink-0 cursor-pointer"
            >
              <span>Continue to Job Prediction</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
