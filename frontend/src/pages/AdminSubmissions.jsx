import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  FileText,
  Users,
  Search,
  Download,
  Trash2,
  Eye,
  X,
  RefreshCw,
  Loader2,
  Calendar,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Lock,
  LogOut,
  AlertCircle,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import {
  getAdminSubmissions,
  getAdminSubmissionDetail,
  deleteAdminSubmission,
} from '../services/api';

const ADMIN_STORAGE_KEY = 'careerai_admin_key';

export default function AdminSubmissions() {
  const [adminKey, setAdminKey] = useState(
    () => sessionStorage.getItem(ADMIN_STORAGE_KEY) || ''
  );
  const [keyInput, setKeyInput] = useState('');
  const [isUnlocked, setIsUnlocked] = useState(
    () => Boolean(sessionStorage.getItem(ADMIN_STORAGE_KEY))
  );

  const [activeTab, setActiveTab] = useState('submissions'); // 'submissions' | 'users'
  const [submissions, setSubmissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Search filter
  const [searchQuery, setSearchQuery] = useState('');

  // Detail Modal State
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // Fetch data whenever unlocked
  const fetchData = async (keyToUse) => {
    const key = keyToUse || adminKey;
    if (!key) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getAdminSubmissions(key);
      setSubmissions(data.submissions || []);
      setUsers(data.users || []);
      setIsUnlocked(true);
      sessionStorage.setItem(ADMIN_STORAGE_KEY, key);
    } catch (err) {
      const status = err.response?.status;
      if (status === 403 || status === 401) {
        setErrorMsg('Invalid Admin Access Key. Access denied.');
        setIsUnlocked(false);
        sessionStorage.removeItem(ADMIN_STORAGE_KEY);
      } else {
        setErrorMsg(err.response?.data?.detail || err.message || 'Failed to fetch admin data.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (adminKey && isUnlocked) {
      fetchData(adminKey);
    }
  }, []);

  const handleUnlock = (e) => {
    e.preventDefault();
    if (!keyInput.trim()) return;
    const cleanKey = keyInput.trim();
    setAdminKey(cleanKey);
    fetchData(cleanKey);
  };

  const handleLock = () => {
    sessionStorage.removeItem(ADMIN_STORAGE_KEY);
    setAdminKey('');
    setKeyInput('');
    setIsUnlocked(false);
    setSubmissions([]);
    setUsers([]);
    setErrorMsg(null);
  };

  const handleViewDetail = async (item) => {
    setIsLoadingDetail(true);
    try {
      const data = await getAdminSubmissionDetail(adminKey, item.id);
      setSelectedSubmission(data.submission);
    } catch (err) {
      // If endpoint fails, fallback to row object
      setSelectedSubmission(item);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to permanently delete submission "${filename}"?`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteAdminSubmission(adminKey, id);
      setSubmissions((prev) => prev.filter((s) => s.id !== id));
      if (selectedSubmission?.id === id) {
        setSelectedSubmission(null);
      }
      setSuccessMsg(`Submission "${filename}" deleted successfully.`);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete submission.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownloadText = (submission) => {
    const text = submission.extracted_text || 'No text extracted.';
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${submission.filename || 'resume'}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Filtered Submissions
  const filteredSubmissions = useMemo(() => {
    if (!searchQuery.trim()) return submissions;
    const q = searchQuery.toLowerCase();
    return submissions.filter((s) => {
      const matchFile = (s.filename || '').toLowerCase().includes(q);
      const matchEmail = (s.user_email || 'guest').toLowerCase().includes(q);
      const matchContact = (s.contact?.email || '').toLowerCase().includes(q) ||
                           (s.contact?.name || '').toLowerCase().includes(q);
      const matchSkills = (s.skills || []).some((sk) => sk.toLowerCase().includes(q));
      return matchFile || matchEmail || matchContact || matchSkills;
    });
  }, [submissions, searchQuery]);

  // Filtered Users
  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) return users;
    const q = searchQuery.toLowerCase();
    return users.filter((u) => {
      const matchName = (u.full_name || '').toLowerCase().includes(q);
      const matchEmail = (u.email || '').toLowerCase().includes(q);
      const matchRole = (u.target_role || '').toLowerCase().includes(q);
      return matchName || matchEmail || matchRole;
    });
  }, [users, searchQuery]);

  // 1. UNLOCK FORM (WHEN NOT AUTHENTICATED AS ADMIN)
  if (!isUnlocked) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200/80 shadow-xl p-8 animate-fadeIn">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-6 mx-auto">
            <Lock className="w-7 h-7" />
          </div>

          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-slate-900">Admin Submissions Viewer</h2>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Protected site owner portal for inspecting all candidate resume submissions and user registrations.
            </p>
          </div>

          {errorMsg && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2.5">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleUnlock} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Admin Access Key
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  placeholder="Enter private admin access key"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  autoFocus
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5">
                Configured via <code className="text-indigo-600 font-mono">ADMIN_ACCESS_KEY</code> in environment.
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading || !keyInput.trim()}
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Key...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Unlock Admin Portal</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // 2. MAIN ADMIN PORTAL (UNLOCKED)
  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12 animate-fadeIn">
      {/* Top Banner & Header */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              <ShieldCheck className="w-3.5 h-3.5" />
              Authenticated Site Owner
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500">Persistent Storage Enabled</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Admin Submissions & Candidate Directory
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Review every resume document uploaded across the platform (both logged-in users and guests) and registered profiles.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => fetchData(adminKey)}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 active:scale-95 transition-all"
            title="Refresh submissions"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            onClick={handleLock}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 active:scale-95 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Lock Portal</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="p-1 text-emerald-600 hover:text-emerald-800">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="p-1 text-rose-600 hover:text-rose-800">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Controls: Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Navigation Tabs */}
        <div className="inline-flex p-1 bg-slate-100 rounded-2xl border border-slate-200/60 w-full sm:w-auto">
          <button
            type="button"
            onClick={() => setActiveTab('submissions')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'submissions'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Uploaded Resumes</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
              activeTab === 'submissions' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'
            }`}>
              {submissions.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('users')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'users'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Registered Users</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
              activeTab === 'users' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'
            }`}>
              {users.length}
            </span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={
              activeTab === 'submissions'
                ? 'Search by candidate, file, skill...'
                : 'Search users by name, email...'
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          />
        </div>
      </div>

      {/* TAB 1: UPLOADED RESUMES */}
      {activeTab === 'submissions' && (
        <div className="space-y-4">
          {filteredSubmissions.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center">
              <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-700">No Resume Submissions Found</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                {searchQuery
                  ? 'No submissions match your search query.'
                  : 'Resumes analyzed on the platform will automatically appear here with full content inspection.'}
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold">
                    <tr>
                      <th className="py-3.5 px-5">Uploaded At</th>
                      <th className="py-3.5 px-5">Candidate / Uploader</th>
                      <th className="py-3.5 px-5">Document</th>
                      <th className="py-3.5 px-5">Extracted Skills</th>
                      <th className="py-3.5 px-5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {filteredSubmissions.map((item) => {
                      const dateStr = item.submitted_at
                        ? new Date(item.submitted_at).toLocaleString()
                        : 'Unknown';
                      const isGuest = !item.user_email && !item.user_id;

                      return (
                        <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                          <td className="py-3.5 px-5 whitespace-nowrap text-slate-500">
                            <div className="flex items-center gap-1.5">
                              <Calendar className="w-3.5 h-3.5 text-slate-400" />
                              <span>{dateStr}</span>
                            </div>
                          </td>

                          <td className="py-3.5 px-5">
                            <div>
                              {isGuest ? (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60">
                                  Guest Visitor
                                </span>
                              ) : (
                                <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                                  <Mail className="w-3.5 h-3.5 text-indigo-500" />
                                  <span>{item.user_email}</span>
                                </div>
                              )}
                              {item.contact?.name && (
                                <p className="text-[11px] text-slate-500 mt-0.5 font-medium">
                                  Name: {item.contact.name}
                                </p>
                              )}
                              {item.contact?.phone && (
                                <p className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                                  <Phone className="w-3 h-3" />
                                  {item.contact.phone}
                                </p>
                              )}
                            </div>
                          </td>

                          <td className="py-3.5 px-5">
                            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-indigo-600" />
                              <span className="truncate max-w-[180px]" title={item.filename}>
                                {item.filename}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                              <span>{item.file_type || 'PDF'}</span>
                              <span>•</span>
                              <span>{item.word_count || 0} words</span>
                            </div>
                          </td>

                          <td className="py-3.5 px-5">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {(item.skills || []).slice(0, 5).map((sk, idx) => (
                                <span
                                  key={idx}
                                  className="inline-block px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-medium"
                                >
                                  {sk}
                                </span>
                              ))}
                              {(item.skills || []).length > 5 && (
                                <span className="text-[10px] text-slate-400 self-center">
                                  +{(item.skills || []).length - 5} more
                                </span>
                              )}
                            </div>
                          </td>

                          <td className="py-3.5 px-5 text-right whitespace-nowrap">
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleViewDetail(item)}
                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold transition-colors"
                                title="View Full Extracted Resume"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                <span>Inspect</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => handleDownloadText(item)}
                                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                                title="Download .txt"
                              >
                                <Download className="w-3.5 h-3.5" />
                              </button>

                              <button
                                type="button"
                                disabled={deletingId === item.id}
                                onClick={() => handleDelete(item.id, item.filename)}
                                className="p-1.5 rounded-lg text-rose-400 hover:text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                                title="Delete submission"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: REGISTERED USERS */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {filteredUsers.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center">
              <Users className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-700">No Registered Users</h3>
              <p className="text-xs text-slate-400 mt-1">
                Registered candidate accounts will appear in this directory.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold">
                    <tr>
                      <th className="py-3.5 px-5">Candidate Name</th>
                      <th className="py-3.5 px-5">Email Address</th>
                      <th className="py-3.5 px-5">Target Career Role</th>
                      <th className="py-3.5 px-5">Experience</th>
                      <th className="py-3.5 px-5">Privacy Mode</th>
                      <th className="py-3.5 px-5 text-right">Joined Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {filteredUsers.map((u) => {
                      const joinedDate = u.created_at
                        ? new Date(u.created_at).toLocaleDateString()
                        : '—';

                      return (
                        <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                          <td className="py-3.5 px-5 font-bold text-slate-900">
                            {u.full_name}
                          </td>
                          <td className="py-3.5 px-5 text-slate-600">
                            {u.email}
                          </td>
                          <td className="py-3.5 px-5">
                            <span className="font-medium text-slate-800">
                              {u.target_role || 'Not specified'}
                            </span>
                          </td>
                          <td className="py-3.5 px-5 text-slate-600">
                            {u.experience_years ? `${u.experience_years} yrs` : '—'}
                          </td>
                          <td className="py-3.5 px-5">
                            {u.save_resume_text ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Opted In
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                                Strict Privacy
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-5 text-right text-slate-500">
                            {joinedDate}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* FULL RESUME INSPECTION MODAL */}
      {selectedSubmission && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    {selectedSubmission.filename}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Uploaded by{' '}
                    <strong className="text-slate-700">
                      {selectedSubmission.user_email || 'Guest Visitor'}
                    </strong>{' '}
                    on{' '}
                    {selectedSubmission.submitted_at
                      ? new Date(selectedSubmission.submitted_at).toLocaleString()
                      : 'Unknown'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDownloadText(selectedSubmission)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download .txt</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedSubmission(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Contact & Statistics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Candidate Contact Info
                  </div>
                  <div className="space-y-1 text-xs">
                    <p className="font-semibold text-slate-900">
                      {selectedSubmission.contact?.name || 'Name Not Detected'}
                    </p>
                    <p className="text-slate-600">
                      {selectedSubmission.contact?.email || 'No email parsed'}
                    </p>
                    <p className="text-slate-600">
                      {selectedSubmission.contact?.phone || 'No phone parsed'}
                    </p>
                    {selectedSubmission.contact?.linkedin && (
                      <p className="text-indigo-600 truncate">
                        {selectedSubmission.contact.linkedin}
                      </p>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60 md:col-span-2">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Extracted Skills ({selectedSubmission.skills?.length || 0})
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                    {(selectedSubmission.skills || []).map((sk, idx) => (
                      <span
                        key={idx}
                        className="inline-block px-2 py-0.5 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-medium"
                      >
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Full Extracted Resume Text */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Full Extracted Resume Text
                  </h4>
                  <span className="text-[11px] text-slate-400">
                    {selectedSubmission.extracted_text?.length || 0} characters
                  </span>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900 text-slate-100 font-mono text-xs leading-relaxed max-h-96 overflow-y-auto whitespace-pre-wrap select-text selection:bg-indigo-500">
                  {selectedSubmission.extracted_text || 'No text extracted from document.'}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => handleDelete(selectedSubmission.id, selectedSubmission.filename)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Submission</span>
              </button>
              <button
                type="button"
                onClick={() => setSelectedSubmission(null)}
                className="px-4 py-1.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-xs font-semibold text-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
