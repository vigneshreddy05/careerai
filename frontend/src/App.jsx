import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './context/AuthContext';
import { ResumeProvider } from './context/ResumeContext';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import ResumeAnalysis from './pages/ResumeAnalysis';
import JobPrediction from './pages/JobPrediction';
import SkillGapAnalysis from './pages/SkillGapAnalysis';
import CareerRoadmap from './pages/CareerRoadmap';
import JobRecommendations from './pages/JobRecommendations';
import CareerAssistant from './pages/CareerAssistant';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import PredictionHistory from './pages/PredictionHistory';
import Login from './pages/Login';
import Register from './pages/Register';

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <ResumeProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<DashboardLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="resume-analysis" element={<ResumeAnalysis />} />
                  <Route path="job-prediction" element={<JobPrediction />} />
                  <Route path="skill-gap" element={<SkillGapAnalysis />} />
                  <Route path="roadmap" element={<CareerRoadmap />} />
                  <Route path="recommendations" element={<JobRecommendations />} />
                  <Route path="history" element={<PredictionHistory />} />
                  <Route path="assistant" element={<CareerAssistant />} />
                  <Route path="settings" element={<Settings />} />
                  <Route path="profile" element={<Profile />} />
                  <Route path="login" element={<Login />} />
                  <Route path="register" element={<Register />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </ResumeProvider>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}
