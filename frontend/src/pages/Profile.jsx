import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  Briefcase,
  Compass,
  Calendar,
  Save,
  Trash2,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, updateProfile, deleteAccount, logout } = useAuth();

  const [fullName, setFullName] = useState('');
  const [currentRole, setCurrentRole] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [experienceYears, setExperienceYears] = useState('0');
  const [saveResumeText, setSaveResumeText] = useState(false);

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setCurrentRole(user.current_role || '');
      setTargetRole(user.target_role || 'Full Stack Software Engineer');
      setExperienceYears(String(user.experience_years ?? 0));
      setSaveResumeText(Boolean(user.save_resume_text));
    }
  }, [user]);

  if (isLoading) {
    return (
      <div className="py-24 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-3" />
        <p className="text-xs text-slate-500">Loading candidate profile...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-6 animate-fadeIn">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto shadow-sm">
          <User className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-1">
            Sign In to Manage Your Profile
          </h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
            Create an account or sign in to customize your target role, configure privacy preferences, and persist your progression history.
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
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
            Create Account
          </Link>
        </div>
      </div>
    );
  }

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    setSaveError(null);

    try {
      await updateProfile({
        full_name: fullName.trim(),
        current_role: currentRole.trim() || null,
        target_role: targetRole.trim() || null,
        experience_years: parseFloat(experienceYears) || 0.0,
        save_resume_text: saveResumeText,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setSaveError(err.message || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteAccount();
      navigate('/', { replace: true });
    } catch (err) {
      alert('Failed to delete account: ' + err.message);
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  // Get user initials
  const initials = user.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'CA';

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {/* Header Profile Summary */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 to-violet-600 text-white font-bold text-xl flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  {user.full_name}
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Active
                </span>
              </div>
              <p className="text-xs text-slate-500 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>{user.email}</span>
                <span className="text-slate-300">•</span>
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Member since {new Date(user.created_at).toLocaleDateString()}</span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={logout}
            className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold transition-colors cursor-pointer self-start sm:self-auto"
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Save Feedback Alerts */}
      {saveSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 animate-fadeIn">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <p className="text-xs font-semibold text-emerald-800">
            Profile attributes and privacy preferences updated successfully!
          </p>
        </div>
      )}

      {saveError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-3 animate-fadeIn">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <p className="text-xs font-semibold text-rose-800">{saveError}</p>
        </div>
      )}

      {/* Main Profile Form Card */}
      <form onSubmit={handleSave} className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Personal & Career Information
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            These settings tune your DistilBERT evaluation benchmarks and roadmap milestone suggestions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Email Address (Account Identifier)
            </label>
            <input
              type="email"
              disabled
              value={user.email}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-100 text-xs text-slate-500 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Current Role / Status
            </label>
            <input
              type="text"
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value)}
              placeholder="e.g. Computer Science Student or Junior Developer"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Years Experience
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              max="50"
              value={experienceYears}
              onChange={(e) => setExperienceYears(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Target Career Role
            </label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer"
            >
              <option value="Full Stack Software Engineer">Full Stack Software Engineer</option>
              <option value="Backend Software Engineer">Backend Software Engineer</option>
              <option value="Frontend Software Engineer">Frontend Software Engineer</option>
              <option value="Cloud & DevOps Engineer">Cloud & DevOps Engineer</option>
              <option value="Data Scientist & ML Practitioner">Data Scientist & ML Practitioner</option>
              <option value="Database Administrator & Data Engineer">Database Administrator & Data Engineer</option>
              <option value="Software QA & Automation Engineer">Software QA & Automation Engineer</option>
            </select>
          </div>
        </div>

        {/* Privacy Section */}
        <div className="pt-4 border-t border-slate-100 space-y-3">
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Data Retention & Privacy Controls
          </h4>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
            <input
              type="checkbox"
              id="profileSaveResume"
              checked={saveResumeText}
              onChange={(e) => setSaveResumeText(e.target.checked)}
              className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
            />
            <label htmlFor="profileSaveResume" className="text-xs text-slate-600 leading-relaxed cursor-pointer">
              <strong>Store sanitized resume text:</strong> When enabled, sanitized resume snippets and skill tokens are securely stored in your local profile database for historical comparisons. When disabled, raw text is processed entirely in memory.
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Saving Profile...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Profile Changes</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Danger Zone: Account Deletion */}
      <div className="bg-white rounded-3xl border border-rose-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-bold text-rose-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Danger Zone: Permanent Account Purge</span>
            </h4>
            <p className="text-xs text-slate-500 mt-1 max-w-xl">
              Permanently delete your user account, stored preferences, and invalidate all active session tokens. This action is irreversible.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowDeleteModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold transition-colors cursor-pointer self-start sm:self-auto"
          >
            <Trash2 className="w-4 h-4 text-rose-600" />
            <span>Delete Account</span>
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-md w-full p-6 sm:p-8 space-y-5 shadow-2xl animate-fadeIn">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="text-center space-y-1">
              <h3 className="text-base font-bold text-slate-900">
                Are you absolutely sure?
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                This will permanently purge your user profile, email registration, and all associated session tokens from the local database.
              </p>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-bold shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Purging...</span>
                  </>
                ) : (
                  <span>Yes, Delete Account</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
