import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  AlertTriangle,
  RefreshCw,
  Loader2,
  FileText,
  ArrowRight,
  TrendingUp,
  Info,
  CheckCircle2,
  Cpu,
  Layers,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';

const DISCLAIMER_TEXT =
  "These scores represent the model's softmax confidence, not calibrated probabilities, semantic similarity scores, or the likelihood of getting hired.";

export default function JobPrediction() {
  const {
    analysisData,
    predictionData,
    isPredicting,
    predictionError,
    fetchJobPrediction,
  } = useResume();

  // Auto-fetch predictions on mount if resume analysis data exists and predictions aren't loaded yet
  useEffect(() => {
    if (analysisData && !predictionData && !isPredicting && !predictionError) {
      const text = analysisData.extracted_text || analysisData.text_preview;
      if (text && text.trim()) {
        fetchJobPrediction(text).catch(() => {
          // Error handled in context state
        });
      }
    }
  }, [analysisData, predictionData, isPredicting, predictionError, fetchJobPrediction]);

  // State 1: No Resume Uploaded Yet
  if (!analysisData) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                DistilBERT Job Role Prediction
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Supervised transformer sequence classification fine-tuned on 24 professional categories.
                Evaluates your resume content using bidirectional self-attention to determine the top 3 matching career domains.
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
            Please upload and analyze a PDF or Word resume first. The extracted text will automatically feed into the DistilBERT inference engine without uploading your file twice.
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

  // State 2: Prediction is Loading
  if (isPredicting) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                DistilBERT Job Role Prediction
              </h2>
              <p className="text-xs text-slate-500">
                Running in-memory sequence classification on {analysisData.filename}...
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-2xl mx-auto py-16 text-center">
          <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-6 shadow-sm">
            <Loader2 className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            Computing Model Inference...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed mb-4">
            Tokenizing resume text blocks and evaluating 24 classification heads with PyTorch CPU inference.
          </p>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 text-[11px] font-medium">
            <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
            <span>Target: 256 subword tokens • Single forward pass</span>
          </div>
        </div>
      </div>
    );
  }

  // State 3: Error State
  if (predictionError) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600 shadow-sm shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Prediction Error
              </h2>
              <p className="text-xs text-slate-500">
                Inference request could not be completed for {analysisData.filename}.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl border border-rose-200/80 p-8 text-center shadow-sm">
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-100 text-rose-800 text-xs mb-6 max-w-md mx-auto">
            {predictionError}
          </div>
          <button
            type="button"
            onClick={() => fetchJobPrediction()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm active:scale-95 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Prediction</span>
          </button>
        </div>
      </div>
    );
  }

  // State 4: Prediction Success View
  const predictions = predictionData?.predictions || [];
  const top1 = predictions[0] || null;
  const isLowConfidence = top1 && (top1.confidence < 0.40 || Boolean(predictionData?.warning));

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <h2 className="text-lg font-bold text-slate-900">
                  DistilBERT Job Role Predictions
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  {predictionData?.model || 'DistilBERT'}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Inference evaluated on extracted text from{' '}
                <span className="font-semibold text-slate-700">{analysisData.filename}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => fetchJobPrediction()}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Re-run Prediction</span>
            </button>
            <Link
              to="/resume-analysis"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100/80 text-indigo-700 text-xs font-semibold transition-colors"
            >
              <span>Resume Overview</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Global Mandatory Disclaimer */}
        <div className="mt-6 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-slate-600 text-xs flex items-start gap-3">
          <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-slate-800">Model Interpretation Notice: </span>
            {DISCLAIMER_TEXT}
          </div>
        </div>
      </div>

      {/* Low-Confidence Warning Banner (Top Score < 0.40) */}
      {isLowConfidence && (
        <div className="bg-amber-50 rounded-3xl border border-amber-200/90 p-5 shadow-sm text-amber-900 flex items-start gap-3 animate-fadeIn">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800">
              Low Prediction Confidence Warning
            </h4>
            <p className="text-xs text-amber-700 leading-relaxed">
              {predictionData?.warning ||
                `The highest confidence score (${(top1.confidence * 100).toFixed(1)}%) is below the 0.40 threshold. The resume content may have cross-domain, sparse, or ambiguous signals.`}
            </p>
            <p className="text-[11px] text-amber-600 italic">
              {DISCLAIMER_TEXT}
            </p>
          </div>
        </div>
      )}

      {/* Top Match Primary Hero Card */}
      {top1 && (
        <div className="bg-gradient-to-br from-white to-indigo-50/30 rounded-3xl border border-indigo-200/80 p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800 text-[11px] font-bold uppercase tracking-wider mb-2">
                <TrendingUp className="w-3 h-3" />
                Rank 1 Primary Prediction
              </span>
              <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                {top1.category.replace(/-/g, ' ')}
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Highest softmax score among the 24 professional categories
              </p>
            </div>

            <div className="text-left sm:text-right">
              <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
                Model Confidence
              </span>
              <span className="text-3xl font-black text-indigo-600 tracking-tight">
                {(top1.confidence * 100).toFixed(1)}%
              </span>
              <span className="text-[11px] text-slate-400 block mt-0.5">
                Softmax confidence
              </span>
            </div>
          </div>

          {/* Large Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200/60">
            <div
              className="bg-gradient-to-r from-indigo-600 to-violet-600 h-3 rounded-full transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(5, top1.confidence * 100))}%` }}
            />
          </div>
        </div>
      )}

      {/* Ranked Top 3 Predictions Grid */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
          Top 3 Candidate Categories (Ranked by Model Confidence)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {predictions.map((pred) => {
            const percent = (pred.confidence * 100).toFixed(1);
            const isRank1 = pred.rank === 1;

            return (
              <div
                key={pred.rank}
                className={`bg-white rounded-2xl border p-5 shadow-sm transition-all flex flex-col justify-between ${
                  isRank1
                    ? 'border-indigo-300 ring-2 ring-indigo-500/10'
                    : 'border-slate-200/80 hover:border-slate-300'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={`text-[11px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        isRank1
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      Rank {pred.rank}
                    </span>
                    <span className="text-sm font-bold text-slate-900">
                      {percent}%
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 tracking-tight mb-1">
                    {pred.category.replace(/-/g, ' ')}
                  </h4>
                  <p className="text-[11px] text-slate-500 leading-snug">
                    Canonical category taxonomy ID #{pred.rank}
                  </p>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        isRank1
                          ? 'bg-indigo-600'
                          : pred.rank === 2
                          ? 'bg-violet-500'
                          : 'bg-slate-400'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(3, pred.confidence * 100))}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-1.5 text-right font-medium">
                    Raw Softmax: {pred.confidence.toFixed(4)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Model Information Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
          Prediction Engine Details
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Model</span>
            <span className="font-semibold text-slate-800 mt-0.5 block">DistilBERT Uncased</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Classes</span>
            <span className="font-semibold text-slate-800 mt-0.5 block">24 Categories</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Sequence Limit</span>
            <span className="font-semibold text-slate-800 mt-0.5 block">256 Subwords</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Device</span>
            <span className="font-semibold text-slate-800 mt-0.5 block">PyTorch CPU (Inference)</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>In-memory inference • Document text is never saved or logged</span>
          <span className="font-medium text-slate-500">CareerAI Phase 9 Engine</span>
        </div>
      </div>

      {/* Next Step Action: Skill Gap & Compatibility Analysis */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-slate-900">
            Next: Semantic Job Description Matching & Skill Gap Analysis
          </h4>
          <p className="text-xs text-slate-500 mt-1">
            Compare your resume directly against specific job postings using Sentence-BERT (all-MiniLM-L6-v2) to identify missing skills.
          </p>
        </div>
        <Link
          to="/skill-gap"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all shrink-0 cursor-pointer"
        >
          <span>Match Against Job Description</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
