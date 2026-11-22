import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Layers,
  Cpu,
  FileText,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Loader2,
  Check,
  X,
  Info,
  TrendingUp,
  Compass,
  Briefcase,
  HelpCircle,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';

const SAMPLE_JOB_DESCRIPTIONS = [
  {
    title: 'Senior Python Engineer',
    description:
      'We are looking for a Senior Python Developer to build and scale cloud microservices. ' +
      'Requirements: 4+ years experience with Python, FastAPI or Django, PostgreSQL, Docker, ' +
      'Kubernetes, Redis, and Amazon Web Services (AWS). Strong knowledge of REST APIs and CI/CD pipelines.',
  },
  {
    title: 'Full Stack React & Node Developer',
    description:
      'Seeking a skilled Full Stack Engineer. Requirements: Strong experience with React, TypeScript, ' +
      'Node.js, Express, Tailwind CSS, and MongoDB. Familiarity with GraphQL, Next.js, and automated testing ' +
      'is highly valued. Experience deploying on AWS or Google Cloud.',
  },
  {
    title: 'Data Scientist / Machine Learning Engineer',
    description:
      'Looking for a Machine Learning Engineer to design and deploy NLP models. ' +
      'Requirements: Strong Python, PyTorch or TensorFlow, Scikit-learn, Pandas, NumPy, and SQL. ' +
      'Experience with transformer models (BERT, Hugging Face) and Docker containerization.',
  },
  {
    title: 'DevOps & Cloud Infrastructure Engineer',
    description:
      'Join our Platform Engineering team. Requirements: In-depth experience with AWS, Kubernetes, ' +
      'Docker, Terraform, Ansible, Linux, and GitHub Actions. Experience managing PostgreSQL databases ' +
      'and Prometheus/Grafana observability stacks.',
  },
];

export default function SkillGapAnalysis() {
  const {
    analysisData,
    matchingData,
    isMatching,
    matchingError,
    executeJobMatch,
    setMatchingData,
  } = useResume();

  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [localError, setLocalError] = useState(null);

  const handleSelectSample = (sample) => {
    setJobTitle(sample.title);
    setJobDescription(sample.description);
    setLocalError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);

    if (!jobDescription || !jobDescription.trim()) {
      setLocalError('Please paste or select a job description to compare.');
      return;
    }

    try {
      await executeJobMatch(jobDescription, jobTitle || null);
    } catch (err) {
      setLocalError(err.message || 'Failed to execute semantic matching.');
    }
  };

  const handleResetMatch = () => {
    setMatchingData(null);
    setLocalError(null);
  };

  // State 1: No Resume Uploaded Yet
  if (!analysisData) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Semantic Resume–Job Description Matching
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Powered by Sentence-BERT (all-MiniLM-L6-v2) and deterministic taxonomy extraction.
                Compare candidate resumes against real job postings to measure conceptual similarity and identify exact skill gaps.
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
            Please upload and analyze a PDF or Word resume first. The extracted resume text will automatically feed into the semantic matching engine without re-uploading.
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

  // Color helper for semantic similarity level
  const getSemanticColor = (level) => {
    switch (level) {
      case 'High Match':
        return {
          bg: 'bg-emerald-50',
          border: 'border-emerald-200/80',
          text: 'text-emerald-800',
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          bar: 'from-emerald-500 to-teal-500',
        };
      case 'Moderate Match':
        return {
          bg: 'bg-indigo-50',
          border: 'border-indigo-200/80',
          text: 'text-indigo-800',
          badge: 'bg-indigo-100 text-indigo-800 border-indigo-300',
          bar: 'from-indigo-500 to-violet-500',
        };
      default:
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200/80',
          text: 'text-amber-800',
          badge: 'bg-amber-100 text-amber-800 border-amber-300',
          bar: 'from-amber-500 to-rose-500',
        };
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Module Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  Semantic Resume–Job Description Matching
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Phase 10 Live
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Dual-engine analysis using <strong>all-MiniLM-L6-v2</strong> dense vector cosine similarity (384 dimensions)
                and deterministic keyword overlap. Comparing candidate: <span className="font-semibold text-slate-700">{analysisData.filename}</span>.
              </p>
            </div>
          </div>

          {matchingData && (
            <button
              type="button"
              onClick={handleResetMatch}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors self-start sm:self-auto cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Compare Another Job</span>
            </button>
          )}
        </div>
      </div>

      {/* Input Section (if no match results yet, or collapsible) */}
      {!matchingData && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Target Job Description Input
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Paste the text of a job posting or select a sample role below to evaluate alignment with your uploaded resume.
            </p>
          </div>

          {/* Sample Role Quick-Select Buttons */}
          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Quick Test: Select Benchmark Job Description
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {SAMPLE_JOB_DESCRIPTIONS.map((sample) => (
                <button
                  key={sample.title}
                  type="button"
                  onClick={() => handleSelectSample(sample)}
                  className={`p-3 rounded-2xl text-left border text-xs font-semibold transition-all cursor-pointer ${
                    jobTitle === sample.title
                      ? 'border-indigo-500 bg-indigo-50/60 text-indigo-900 shadow-sm'
                      : 'border-slate-200/80 hover:border-indigo-300 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="truncate">{sample.title}</span>
                    <Sparkles className="w-3 h-3 text-indigo-500 shrink-0" />
                  </div>
                  <p className="text-[10px] text-slate-400 font-normal line-clamp-2">
                    {sample.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Job Title (Optional)
              </label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Job Description Text <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={6}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the complete job description, requirements, and responsibilities here..."
                className="w-full p-4 rounded-2xl border border-slate-200 text-xs leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-sans"
              />
            </div>

            {(localError || matchingError) && (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                <div>
                  <p className="font-semibold">Matching Error</p>
                  <p className="text-rose-600 mt-0.5">{localError || matchingError}</p>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isMatching || !jobDescription.trim()}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
            >
              {isMatching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Computing Semantic Vectors & Skill Matrix...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run Dual-Engine Matching Analysis</span>
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Loading Overlay State */}
      {isMatching && !matchingData && (
        <div className="max-w-2xl mx-auto py-16 text-center animate-fadeIn">
          <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-6 shadow-sm">
            <Cpu className="w-8 h-8 animate-pulse" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            Encoding Semantic Embeddings on CPU...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Generating 384-dimensional dense vectors with all-MiniLM-L6-v2, computing attention-mask mean pooling, and extracting deterministic skill intersections.
          </p>
        </div>
      )}

      {/* Results View */}
      {matchingData && (
        <div className="space-y-6 animate-fadeIn">
          {/* Target Role Banner */}
          {matchingData.job_title && (
            <div className="bg-slate-900 text-white rounded-3xl p-6 sm:p-7 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/20 text-slate-200 border border-white/20">
                  Target Evaluation Role
                </span>
                <h3 className="text-lg font-bold text-white mt-1.5">
                  {matchingData.job_title}
                </h3>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Evaluated against resume: <strong>{analysisData.filename}</strong></span>
              </div>
            </div>
          )}

          {/* Dual-Engine Score Overview Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card A: Semantic Similarity (Sentence-BERT) */}
            {(() => {
              const sem = matchingData.semantic_match;
              const color = getSemanticColor(sem.similarity_level);
              return (
                <div className={`rounded-3xl border ${color.border} ${color.bg} p-6 sm:p-8 shadow-sm flex flex-col justify-between`}>
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-xl bg-white/80 border border-slate-200/60 flex items-center justify-center text-indigo-600 shadow-sm">
                          <Cpu className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                            Engine A: Semantic Similarity
                          </h4>
                          <p className="text-[11px] text-slate-500">Sentence-BERT (all-MiniLM-L6-v2)</p>
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${color.badge}`}>
                        {sem.similarity_level}
                      </span>
                    </div>

                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-4xl sm:text-5xl font-black tracking-tight text-slate-900">
                        {sem.similarity_percentage}%
                      </span>
                      <span className="text-xs font-semibold text-slate-500">
                        ({sem.similarity_score} cosine similarity)
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-3 rounded-full bg-white/60 border border-slate-200/60 overflow-hidden mb-4 p-0.5">
                      <div
                        className={`h-full rounded-full bg-gradient-to-r ${color.bar} transition-all duration-700`}
                        style={{ width: `${sem.similarity_percentage}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-200/60 text-[11px] text-slate-600 space-y-1">
                    <p className="flex items-center justify-between">
                      <span>Embedding Dimensionality:</span>
                      <strong className="text-slate-800">{sem.embedding_dimension} dimensions</strong>
                    </p>
                    <p className="flex items-center justify-between">
                      <span>Document Chunks Processed:</span>
                      <strong className="text-slate-800">
                        Resume: {sem.chunk_count_resume} • Job: {sem.chunk_count_job}
                      </strong>
                    </p>
                  </div>
                </div>
              );
            })()}

            {/* Card B: Deterministic Skill Match */}
            {(() => {
              const sk = matchingData.skill_match;
              return (
                <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm">
                          <CheckCircle2 className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                            Engine B: Skill Coverage
                          </h4>
                          <p className="text-[11px] text-slate-500">Exact Taxonomy & Boundary Matching</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                        {sk.matched_count} / {sk.total_jd_skills} Skills
                      </span>
                    </div>

                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-4xl sm:text-5xl font-black tracking-tight text-slate-900">
                        {sk.match_percentage}%
                      </span>
                      <span className="text-xs font-semibold text-slate-500">
                        verified keyword coverage
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-3 rounded-full bg-slate-100 border border-slate-200/60 overflow-hidden mb-4 p-0.5">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                        style={{ width: `${sk.match_percentage}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-600 space-y-1">
                    <p className="flex items-center justify-between">
                      <span>Matching Requirements:</span>
                      <strong className="text-emerald-600 font-bold">{sk.matching_skills.length} skills</strong>
                    </p>
                    <p className="flex items-center justify-between">
                      <span>Identified Skill Gaps:</span>
                      <strong className="text-rose-600 font-bold">{sk.missing_skills.length} missing</strong>
                    </p>
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Mandatory Project Disclaimer Card */}
          <div className="rounded-3xl bg-amber-50/70 border border-amber-200/80 p-5 sm:p-6 shadow-sm flex items-start gap-3.5">
            <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h5 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-0.5">
                Metric Evaluation Advisory
              </h5>
              <p className="text-xs text-amber-900/80 leading-relaxed">
                {matchingData.disclaimer}
              </p>
            </div>
          </div>

          {/* Detailed Skill Breakdown Sections */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 tracking-tight">
                  Detailed Skill Intersection Breakdown
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Extracted via curated technical dictionary and regex boundary verification
                </p>
              </div>
            </div>

            {/* 1. Matching Skills */}
            <div className="p-5 rounded-2xl bg-emerald-50/50 border border-emerald-100">
              <div className="flex items-center gap-2 mb-3">
                <Check className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-bold text-emerald-900">
                  Matching Skills ({matchingData.skill_match.matching_skills.length})
                </span>
                <span className="text-[10px] text-emerald-600 font-medium">
                  • Verified in both your resume and the job description
                </span>
              </div>
              {matchingData.skill_match.matching_skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {matchingData.skill_match.matching_skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-2xs"
                    >
                      <Check className="w-3 h-3 text-emerald-600" />
                      <span>{skill}</span>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No exact technical skill matches detected.</p>
              )}
            </div>

            {/* 2. Missing Skills (Skill Gaps) */}
            <div className="p-5 rounded-2xl bg-rose-50/50 border border-rose-100">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span className="text-xs font-bold text-rose-900">
                  Skill Gaps / Missing Requirements ({matchingData.skill_match.missing_skills.length})
                </span>
                <span className="text-[10px] text-rose-600 font-medium">
                  • Present in job description but not detected in resume
                </span>
              </div>
              {matchingData.skill_match.missing_skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {matchingData.skill_match.missing_skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-rose-200 text-xs font-semibold text-rose-800 shadow-2xs"
                    >
                      <X className="w-3 h-3 text-rose-600" />
                      <span>{skill}</span>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-emerald-600 font-medium">
                  Congratulations! All technical skills from the job description are present in your resume.
                </p>
              )}
            </div>

            {/* 3. Additional Resume Skills */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-slate-500" />
                <span className="text-xs font-bold text-slate-800">
                  Additional Resume Skills ({matchingData.skill_match.additional_skills.length})
                </span>
                <span className="text-[10px] text-slate-400 font-medium">
                  • Found on your resume, not explicitly requested in this job posting
                </span>
              </div>
              {matchingData.skill_match.additional_skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {matchingData.skill_match.additional_skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 text-xs font-medium text-slate-700"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No extra skills detected.</p>
              )}
            </div>
          </div>

          {/* Actionable Suggestions Card */}
          {matchingData.suggestions && matchingData.suggestions.length > 0 && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900 tracking-tight">
                  Tailored Optimization Recommendations
                </h3>
              </div>
              <div className="space-y-3">
                {matchingData.suggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-indigo-50/40 border border-indigo-100/80 flex items-start gap-3"
                  >
                    <div className="w-6 h-6 rounded-lg bg-indigo-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {suggestion}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Action to Next Phase */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Ready to Bridge Your Skill Gaps?
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Explore tailored career paths or view a structured 30/60-day personalized learning roadmap.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/recommendations"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold transition-all shrink-0 cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span>Career Recommendations</span>
              </Link>
              <Link
                to="/roadmap"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all shrink-0 cursor-pointer"
              >
                <Compass className="w-4 h-4" />
                <span>Build Learning Roadmap</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
