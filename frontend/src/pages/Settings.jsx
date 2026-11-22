import React from 'react';
import { Link } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  User,
  ShieldCheck,
  Cpu,
  Lock,
  ExternalLink,
  LogOut,
  Database,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
            <SettingsIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-bold tracking-tight text-slate-900">
                System Settings & Privacy Controls
              </h2>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                System Active
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
              Configure session security, view local model deployment parameters, and inspect privacy and data retention preferences.
            </p>
          </div>
        </div>
      </div>

      {/* Account Profile Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Account Credentials & Profile</h3>
              <p className="text-xs text-slate-500">
                {isAuthenticated
                  ? `Signed in as ${user.email} (${user.full_name})`
                  : 'Currently operating in Guest Explorer mode'}
              </p>
            </div>
          </div>

          {isAuthenticated ? (
            <Link
              to="/profile"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
            >
              <span>Manage Profile</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-sm"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Local AI Architecture & Hardware Status */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Local Machine Learning Pipeline</h3>
            <p className="text-xs text-slate-500">Hardware verification and model runtime status</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Model A (Classifier)
            </span>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-800">DistilBERT 24-Class</span>
            </div>
            <p className="text-[11px] text-slate-500">Local CPU PyTorch Inference</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Model B (Semantic Matcher)
            </span>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-800">Sentence-BERT MiniLM</span>
            </div>
            <p className="text-[11px] text-slate-500">Cosine Vector Comparison</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Data Storage
            </span>
            <div className="flex items-center gap-1.5">
              <Database className="w-4 h-4 text-indigo-600" />
              <span className="text-xs font-bold text-slate-800">SQLite Offline / Mongo</span>
            </div>
            <p className="text-[11px] text-slate-500">100% Offline Local Persistence</p>
          </div>
        </div>
      </div>

      {/* Privacy & Ethical Guardrail Guarantees */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-3">
        <div className="flex items-center gap-3 pb-2 border-b border-slate-100">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Privacy & Ethical Standards</h3>
            <p className="text-xs text-slate-500">Guaranteed data protection and transparent AI principles</p>
          </div>
        </div>

        <ul className="space-y-2 pt-1 text-xs text-slate-600">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
            <span>
              <strong>Zero External Transmission:</strong> Resumes are parsed locally on your laptop using PyMuPDF and python-docx. No resume text is sent to third-party cloud APIs.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
            <span>
              <strong>Ethical Expectation Advisory:</strong> Model confidence percentages represent statistical classifier output and semantic cosine distance, not guaranteed hiring probability or placement guarantees.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
            <span>
              <strong>Full Cascading Deletion Rights:</strong> You can purge your account, saved roadmaps, and cached metrics at any time with one click.
            </span>
          </li>
        </ul>
      </div>

      {/* Site Administration Portal Card */}
      <div className="bg-slate-50 rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-100/70 border border-indigo-200/60 flex items-center justify-center text-indigo-700">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">Site Owner Portal</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Access the protected submissions viewer and registered candidate directory.
            </p>
          </div>
        </div>
        <Link
          to="/admin"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold shadow-xs transition-colors"
        >
          <span>Admin Portal</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Sign Out Card */}
      {isAuthenticated && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">End Session</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Invalidate your active JWT session token on this device.
            </p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-700 text-xs font-bold transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
}
