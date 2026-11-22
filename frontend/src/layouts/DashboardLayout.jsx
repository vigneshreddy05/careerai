import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import UploadModal from '../components/UploadModal';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50/70 text-slate-800 flex">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-72 transition-all">
        {/* Top Header */}
        <Header
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenUploadModal={() => setUploadModalOpen(true)}
        />

        {/* Dynamic Page Views */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet context={{ openUploadModal: () => setUploadModalOpen(true) }} />
        </main>

        {/* Footer Note */}
        <footer className="border-t border-slate-200/60 bg-white/50 px-6 py-4 text-center text-[11px] text-slate-400">
          CareerAI v0.1.0 • Privacy-First AI Job Prediction & Career Recommendation Platform
        </footer>
      </div>

      {/* Quick Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />
    </div>
  );
}
