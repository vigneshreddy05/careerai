import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useResume } from '../context/ResumeContext';

export default function UploadModal({ isOpen, onClose }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [localError, setLocalError] = useState(null);
  const { uploadFile, isLoading, uploadProgress } = useResume();
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setLocalError(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    setLocalError(null);
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.pdf') && !lowerName.endsWith('.docx')) {
      setLocalError('Unsupported format. Please select a PDF (.pdf) or DOCX (.docx) file.');
      setSelectedFile(null);
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setLocalError('File size exceeds the 5 MB limit.');
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setLocalError(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    try {
      await uploadFile(selectedFile);
      onClose();
      navigate('/resume-analysis');
    } catch (err) {
      setLocalError(err.message || 'Failed to analyze resume.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">Upload Your Resume</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Supports PDF and DOCX formats (Max 5 MB)
            </p>
          </div>
          <button
            type="button"
            disabled={isLoading}
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload Body */}
        <div className="p-6">
          {/* Error Banner */}
          {localError && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{localError}</span>
            </div>
          )}

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center flex flex-col items-center justify-center transition-all ${
              dragActive
                ? 'border-indigo-500 bg-indigo-50/50 scale-[0.99]'
                : 'border-slate-200 hover:border-indigo-300 bg-slate-50/60'
            }`}
          >
            <div className="w-14 h-14 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm shadow-indigo-100">
              {isLoading ? (
                <Loader2 className="w-7 h-7 animate-spin" />
              ) : (
                <UploadCloud className="w-7 h-7" />
              )}
            </div>

            <p className="text-sm font-semibold text-slate-800 mb-1">
              {selectedFile ? selectedFile.name : 'Drag & drop your resume file here'}
            </p>
            <p className="text-xs text-slate-400 mb-4">
              {selectedFile
                ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze`
                : 'or browse from your local storage'}
            </p>

            <label className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold shadow-sm hover:bg-slate-50 cursor-pointer transition-colors ${
              isLoading ? 'opacity-50 pointer-events-none' : ''
            }`}>
              <FileText className="w-4 h-4 text-slate-500" />
              <span>{selectedFile ? 'Change File' : 'Browse Files'}</span>
              <input
                type="file"
                accept=".pdf,.docx"
                disabled={isLoading}
                onChange={handleChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Upload Progress Bar */}
          {isLoading && (
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5 font-medium">
                <span>Analyzing document...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress || 10}%` }}
                />
              </div>
            </div>
          )}

          {/* Privacy Note */}
          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200/60 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <p className="text-[11px] text-slate-500 leading-relaxed">
              <strong className="text-slate-700">In-Memory Privacy:</strong> Processed in memory by PyMuPDF and python-docx. Your document is never permanently saved to disk or database.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-slate-50/80 border-t border-slate-100">
          <button
            type="button"
            disabled={isLoading}
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!selectedFile || isLoading}
            onClick={handleSubmit}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white shadow-sm transition-all ${
              selectedFile && !isLoading
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-500/20 active:scale-95'
                : 'bg-slate-300 cursor-not-allowed'
            }`}
          >
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>{isLoading ? 'Processing...' : 'Start AI Analysis'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
