import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  History,
  FileText,
  Briefcase,
  CheckCircle2,
  Trash2,
  ExternalLink,
  Loader2,
  AlertCircle,
  ShieldCheck,
  Calendar,
  Sparkles,
  ArrowRight,
  Target,
  Compass,
  Lock,
} from 'lucide-react';
import { getHistoryList, deleteHistoryItem, clearAllHistory } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useResume } from '../context/ResumeContext';

export default function PredictionHistory() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { loadHistoryRecord } = useResume();

  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Loading specific record into workspace
  const [loadingRecordId, setLoadingRecordId] = useState(null);

  // Delete modal state
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Clear all modal state
  const [showClearModal, setShowClearModal] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  const fetchHistory = async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await getHistoryList();
      setRecords(data.records || []);
    } catch (err) {
      setError(err.message || 'Failed to load historical evaluation records.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [isAuthenticated]);

  const handleLoadRecord = async (recordId) => {
    setLoadingRecordId(recordId);
    try {
      await loadHistoryRecord(recordId);
      navigate('/resume-analysis');
    } catch (err) {
      alert('Failed to load historical workspace snapshot: ' + err.message);
    } finally {
      setLoadingRecordId(null);
    }
  };

  const handleDeleteRecord = async () => {
    if (!deleteTargetId) return;
    setIsDeleting(true);
    try {
      await deleteHistoryItem(deleteTargetId);
      setRecords((prev) => prev.filter((r) => r.id !== deleteTargetId));
      setDeleteTargetId(null);
    } catch (err) {
      alert('Failed to delete history record: ' + err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClearAll = async () => {
    setIsClearing(true);
    try {
      await clearAllHistory();
      setRecords([]);
      setShowClearModal(false);
    } catch (err) {
      alert('Failed to clear history: ' + err.message);
    } finally {
      setIsClearing(false);
    }
  };

  // State 1: Guest Mode
  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <History className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1">
                Prediction & Evaluation History
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Persistent timeline of past resume analyses, DistilBERT job-role classifications, Sentence-BERT semantic matches, and progression roadmaps.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-sm space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-sm">
            <Lock className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-900">
            Sign In to Enable Persistent Analysis History
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Guest analyses run 100% in memory and disappear when you refresh or close the tab. Create a free account or sign in to save your evaluations, track skill growth over time, and reload past sessions with one click.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              to="/login"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold transition-colors"
            >
              Create Free Account
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
              <History className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  Prediction & Evaluation History
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {records.length} Saved
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
                Browse, compare, and restore previously evaluated candidate resumes with their complete DistilBERT classification, semantic match, and milestone records.
              </p>
            </div>
          </div>

          {records.length > 0 && (
            <button
              type="button"
              onClick={() => setShowClearModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold transition-colors cursor-pointer self-start sm:self-auto"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear All History</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <p className="text-xs font-semibold text-rose-800">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="py-24 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-3" />
          <p className="text-xs text-slate-500">Retrieving historical evaluation timeline...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && records.length === 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-sm space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-900">
            No Saved Analyses Yet
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Upload and analyze a resume document. Your evaluations, DistilBERT predictions, and roadmaps will automatically appear here for historical tracking.
          </p>
          <Link
            to="/resume-analysis"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all"
          >
            <span>Analyze a Resume Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Records Grid */}
      {!isLoading && records.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {records.map((item) => {
            const isRestoring = loadingRecordId === item.id;
            return (
              <div
                key={item.id}
                className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm flex flex-col justify-between hover:border-indigo-300 transition-all space-y-4"
              >
                <div>
                  {/* Top Bar: Filename & Timestamp */}
                  <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                        <h4 className="text-sm font-bold text-slate-900 truncate">
                          {item.filename}
                        </h4>
                      </div>
                      <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(item.created_at).toLocaleString()}</span>
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setDeleteTargetId(item.id)}
                      title="Delete this record"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Highlights Grid */}
                  <div className="grid grid-cols-2 gap-3 pt-3">
                    <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Extracted Skills
                      </span>
                      <strong className="text-sm font-black text-slate-900">
                        {item.skill_count} Technical Skills
                      </strong>
                    </div>

                    <div className="p-3 rounded-2xl bg-indigo-50/60 border border-indigo-100">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 block mb-0.5">
                        DistilBERT Category
                      </span>
                      <strong className="text-xs font-bold text-indigo-950 truncate block">
                        {item.top_role || 'Not Classified'}
                      </strong>
                      {item.top_confidence && (
                        <span className="text-[10px] font-semibold text-indigo-700">
                          {(item.top_confidence * 100).toFixed(1)}% Confidence
                        </span>
                      )}
                    </div>

                    {item.latest_job_title && (
                      <div className="p-3 rounded-2xl bg-emerald-50/60 border border-emerald-100 col-span-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block mb-0.5">
                          Latest Sentence-BERT Match
                        </span>
                        <div className="flex items-center justify-between text-xs font-bold text-emerald-950">
                          <span className="truncate">{item.latest_job_title}</span>
                          <span>
                            {item.latest_match_score ? `${Number(item.latest_match_score).toFixed(1)}%` : ''}
                          </span>
                        </div>
                      </div>
                    )}

                    {item.target_roadmap_role && (
                      <div className="p-3 rounded-2xl bg-violet-50/60 border border-violet-100 col-span-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-violet-700 block mb-0.5">
                          Target Progression Track
                        </span>
                        <span className="text-xs font-bold text-violet-950 block truncate">
                          {item.target_roadmap_role}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer: Privacy status & Load in Workspace */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>
                      {item.has_extracted_text ? 'Text Stored' : 'Text Stripped (Privacy Opt-out)'}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleLoadRecord(item.id)}
                    disabled={isRestoring}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
                  >
                    {isRestoring ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Restoring...</span>
                      </>
                    ) : (
                      <>
                        <span>Load in Workspace</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Record Confirmation Modal */}
      {deleteTargetId && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-sm w-full p-6 space-y-4 shadow-2xl animate-fadeIn">
            <h4 className="text-sm font-bold text-slate-900">Delete Analysis Record?</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Are you sure you want to delete this historical analysis? This cannot be undone.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteTargetId(null)}
                disabled={isDeleting}
                className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteRecord}
                disabled={isDeleting}
                className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-xs font-bold text-white shadow-sm cursor-pointer"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear All History Confirmation Modal */}
      {showClearModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-sm w-full p-6 space-y-4 shadow-2xl animate-fadeIn">
            <h4 className="text-sm font-bold text-slate-900">Clear All History?</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              This will permanently purge all {records.length} historical resume evaluations from your local database.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowClearModal(false)}
                disabled={isClearing}
                className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearAll}
                disabled={isClearing}
                className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-xs font-bold text-white shadow-sm cursor-pointer"
              >
                {isClearing ? 'Clearing...' : 'Yes, Clear All'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
