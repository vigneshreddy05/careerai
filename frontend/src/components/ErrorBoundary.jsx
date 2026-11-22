import React from 'react';
import { AlertTriangle, RefreshCw, Home, ChevronDown, ChevronUp } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('CareerAI Uncaught Frontend Error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-slate-800">
          <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xl text-center space-y-6">
            <div className="w-16 h-16 rounded-3xl bg-rose-50 border border-rose-100 text-rose-600 flex items-center justify-center mx-auto shadow-sm">
              <AlertTriangle className="w-8 h-8" />
            </div>

            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 mb-1.5">
                Something Went Wrong
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                An unexpected error occurred while rendering the page. Your active session data remains safely cached.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleReload}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-xs font-bold shadow-sm shadow-indigo-500/20 hover:from-indigo-500 hover:to-violet-500 transition-all cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Page</span>
              </button>
              <button
                type="button"
                onClick={this.handleGoHome}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 text-xs font-bold transition-all cursor-pointer"
              >
                <Home className="w-3.5 h-3.5" />
                <span>Return to Dashboard</span>
              </button>
            </div>

            {/* Collapsible Error Diagnostics */}
            {this.state.error && (
              <div className="pt-4 border-t border-slate-100 text-left">
                <button
                  type="button"
                  onClick={() => this.setState((prev) => ({ showDetails: !prev.showDetails }))}
                  className="flex items-center justify-between w-full text-[11px] font-semibold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  <span>Technical Diagnostics</span>
                  {this.state.showDetails ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                </button>

                {this.state.showDetails && (
                  <pre className="mt-2 p-3 rounded-xl bg-slate-900 text-rose-300 font-mono text-[10px] overflow-x-auto max-h-40 whitespace-pre-wrap leading-relaxed">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
