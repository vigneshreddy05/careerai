import React, { useState, useRef, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import {
  Menu,
  Search,
  Bell,
  UploadCloud,
  Sparkles,
  ShieldCheck,
  User,
  LogOut,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const routeTitles = {
  '/': 'Career Dashboard',
  '/resume-analysis': 'Resume Analysis & Skills',
  '/job-prediction': 'BERT Job Prediction',
  '/skill-gap': 'Skill Gap Analysis',
  '/roadmap': 'Career Progression Roadmap',
  '/recommendations': 'Job Recommendations',
  '/assistant': 'AI Career Assistant',
  '/settings': 'System Settings & Privacy',
  '/profile': 'Candidate Profile Management',
  '/login': 'Account Sign In',
  '/register': 'Create Candidate Account',
};

export default function Header({ onOpenSidebar, onOpenUploadModal }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentTitle = routeTitles[location.pathname] || 'Dashboard';

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProfileDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'CA';

  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-30 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="p-2 -ml-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg lg:hidden cursor-pointer"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900">
            {currentTitle}
          </h1>
        </div>
      </div>

      {/* Center: Search Field */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-4">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search skills, job roles, learning modules..."
            className="w-full pl-9 pr-12 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-800 placeholder-slate-400"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-200">
            ⌘K
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Local AI Engine Badge */}
        <div className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 text-[11px] font-medium">
          <ShieldCheck className="w-3 h-3 text-emerald-500" />
          <span>Local Engine Active</span>
        </div>

        {/* Upload Resume Quick CTA */}
        <button
          type="button"
          onClick={onOpenUploadModal}
          className="inline-flex items-center gap-2 px-3 sm:px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-sm shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
        >
          <UploadCloud className="w-4 h-4" />
          <span className="hidden sm:inline">Upload Resume</span>
          <span className="sm:hidden">Upload</span>
        </button>

        {/* Notifications Icon */}
        <button
          type="button"
          className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          aria-label="View notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-600 ring-2 ring-white" />
        </button>

        {/* Profile Avatar & Dropdown or Guest Sign In */}
        <div className="relative pl-2 border-l border-slate-200" ref={dropdownRef}>
          {isAuthenticated ? (
            <div>
              <button
                type="button"
                onClick={() => setProfileDropdownOpen((prev) => !prev)}
                className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer group"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white font-semibold text-xs flex items-center justify-center shadow-sm">
                  {initials}
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 hidden sm:block" />
              </button>

              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-slate-200 shadow-xl py-2 z-50 animate-fadeIn">
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="text-xs font-bold text-slate-900 truncate">{user.full_name}</p>
                    <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
                  </div>

                  <Link
                    to="/profile"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    <User className="w-4 h-4 text-slate-400" />
                    <span>My Profile</span>
                  </Link>

                  <Link
                    to="/settings"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    <Settings className="w-4 h-4 text-slate-400" />
                    <span>Settings & Privacy</span>
                  </Link>

                  <div className="pt-1 mt-1 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer text-left"
                    >
                      <LogOut className="w-4 h-4 text-rose-500" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all shadow-sm"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
