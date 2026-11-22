import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  CheckCircle2,
  Compass,
  Sparkles,
  History,
  Bot,
  Settings,
  X,
  User,
  ShieldCheck,
  ChevronRight,
  LogIn,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navigationItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Resume Analysis', path: '/resume-analysis', icon: FileText },
  { name: 'Job Prediction', path: '/job-prediction', icon: Briefcase },
  { name: 'Skill Gap Analysis', path: '/skill-gap', icon: CheckCircle2 },
  { name: 'Career Roadmap', path: '/roadmap', icon: Compass },
  { name: 'Job Recommendations', path: '/recommendations', icon: Sparkles },
  { name: 'Prediction History', path: '/history', icon: History },
  { name: 'AI Career Assistant', path: '/assistant', icon: Bot },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar({ isOpen, onClose }) {
  const { user, isAuthenticated } = useAuth();

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'CA';
  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-white border-r border-slate-200/80 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100">
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 bg-clip-text text-transparent">
                  CareerAI
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Pro
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-500">AI Career Copilot</p>
            </div>
          </NavLink>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Main Navigation Menu */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-1.5">
          <div className="px-3 pb-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Core Modules
            </p>
          </div>

          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth < 1024) onClose();
                }}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-50 to-violet-50/50 text-indigo-700 shadow-sm border border-indigo-100/80 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/80'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive
                            ? 'text-indigo-600'
                            : 'text-slate-400 group-hover:text-slate-600'
                        }`}
                      />
                      <span>{item.name}</span>
                    </div>
                    {isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Privacy & System Status Indicator */}
        <div className="px-4 py-3 mx-4 mb-3 rounded-xl bg-slate-50 border border-slate-200/60">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-semibold text-slate-700">Local AI Engine</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            DistilBERT & Ollama 3B running with privacy-first CPU pipeline.
          </p>
        </div>

        {/* User Profile Card at Bottom */}
        <div className="p-4 border-t border-slate-100 bg-white">
          {isAuthenticated ? (
            <Link
              to="/profile"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white font-semibold text-xs flex items-center justify-center ring-2 ring-indigo-50 shrink-0">
                  {initials}
                </div>
                <div className="overflow-hidden min-w-0">
                  <p className="text-xs font-semibold text-slate-800 truncate group-hover:text-indigo-600 transition-colors">
                    {user.full_name}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">
                    {user.current_role || user.email}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 shrink-0 transition-colors" />
            </Link>
          ) : (
            <Link
              to="/login"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-full bg-slate-100 text-slate-600 font-semibold text-xs flex items-center justify-center ring-2 ring-slate-200/60 shrink-0">
                  <LogIn className="w-4 h-4" />
                </div>
                <div className="overflow-hidden min-w-0">
                  <p className="text-xs font-semibold text-slate-800 truncate group-hover:text-indigo-600 transition-colors">
                    Guest Explorer
                  </p>
                  <p className="text-[11px] text-indigo-600 font-medium truncate">
                    Sign in to save profile
                  </p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 shrink-0 transition-colors" />
            </Link>
          )}
        </div>
      </aside>
    </>
  );
}
