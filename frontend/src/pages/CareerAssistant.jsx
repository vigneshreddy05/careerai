import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Send,
  Sparkles,
  RefreshCw,
  Cpu,
  Zap,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Target,
  FileText,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Loader2,
  Trash2,
  HelpCircle,
  Compass,
} from 'lucide-react';
import { useResume } from '../context/ResumeContext';
import { getAssistantStatus, sendAssistantMessage } from '../services/api';

/**
 * Lightweight, accessible Markdown renderer for formatted assistant responses.
 */
function MarkdownText({ content }) {
  const lines = content.split('\n');
  const elements = [];
  let currentList = [];
  let inBlockquote = false;
  let blockquoteLines = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc list-outside ml-5 space-y-1 my-2 text-xs leading-relaxed text-slate-700">
          {currentList.map((item, idx) => (
            <li key={idx} dangerouslySetInnerHTML={{ __html: formatInline(item) }} />
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  const flushBlockquote = () => {
    if (blockquoteLines.length > 0) {
      elements.push(
        <div key={`bq-${elements.length}`} className="p-3 my-2 rounded-xl bg-indigo-50/70 border-l-4 border-indigo-500 text-xs italic text-indigo-950 leading-relaxed">
          {blockquoteLines.join(' ')}
        </div>
      );
      blockquoteLines = [];
      inBlockquote = false;
    }
  };

  const formatInline = (str) => {
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-900">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-slate-800">$1</em>')
      .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-slate-100 text-indigo-700 font-mono text-[11px] border border-slate-200/60">$1</code>');
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Headers
    if (trimmed.startsWith('#### ')) {
      flushList();
      flushBlockquote();
      elements.push(
        <h5 key={idx} className="text-xs font-bold text-slate-900 uppercase tracking-wider mt-3 mb-1" dangerouslySetInnerHTML={{ __html: formatInline(trimmed.slice(5)) }} />
      );
      return;
    }
    if (trimmed.startsWith('### ')) {
      flushList();
      flushBlockquote();
      elements.push(
        <h4 key={idx} className="text-sm font-bold text-slate-900 mt-4 mb-1.5 flex items-center gap-1.5" dangerouslySetInnerHTML={{ __html: formatInline(trimmed.slice(4)) }} />
      );
      return;
    }

    // Blockquotes
    if (trimmed.startsWith('> ')) {
      flushList();
      inBlockquote = true;
      blockquoteLines.push(trimmed.slice(2));
      return;
    } else if (inBlockquote) {
      flushBlockquote();
    }

    // Bullet points
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      currentList.push(trimmed.slice(2));
      return;
    } else {
      flushList();
    }

    // Empty lines
    if (!trimmed) {
      return;
    }

    // Numbered lists (e.g. "1. ")
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      elements.push(
        <div key={idx} className="flex items-start gap-2 text-xs leading-relaxed text-slate-700 my-1.5">
          <span className="font-bold text-indigo-600 shrink-0">{numMatch[1]}.</span>
          <div dangerouslySetInnerHTML={{ __html: formatInline(numMatch[2]) }} />
        </div>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <p key={idx} className="text-xs text-slate-700 leading-relaxed my-1.5" dangerouslySetInnerHTML={{ __html: formatInline(trimmed) }} />
    );
  });

  flushList();
  flushBlockquote();

  return <div className="space-y-1">{elements}</div>;
}

export default function CareerAssistant() {
  const {
    analysisData,
    predictionData,
    matchingData,
    roadmapData,
    suggestionsData,
    selectedTargetRole,
  } = useResume();

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoadingReply, setIsLoadingReply] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Runtime and Engine state
  const [ollamaStatus, setOllamaStatus] = useState({
    ollama_available: false,
    ollama_base_url: 'http://127.0.0.1:11434',
    configured_model: 'qwen2.5:3b',
    status: 'checking',
  });
  const [useLocalLlm, setUseLocalLlm] = useState(true);
  const [showContextDetails, setShowContextDetails] = useState(false);

  const messagesEndRef = useRef(null);

  // Probe Ollama status on page load
  useEffect(() => {
    let isMounted = true;
    async function checkStatus() {
      try {
        const res = await getAssistantStatus();
        if (isMounted) {
          setOllamaStatus(res);
        }
      } catch (err) {
        if (isMounted) {
          setOllamaStatus({
            ollama_available: false,
            ollama_base_url: 'http://127.0.0.1:11434',
            configured_model: 'qwen2.5:3b',
            status: 'offline',
          });
        }
      }
    }
    checkStatus();
    return () => {
      isMounted = false;
    };
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoadingReply]);

  // Build sanitized, PII-scrubbed context payload from active workspace
  const buildContextPayload = () => {
    const skillsList = analysisData?.skills?.all_skills || [];
    const targetRole =
      selectedTargetRole ||
      roadmapData?.roadmap?.role_title ||
      matchingData?.job_title ||
      null;

    const missingSkills =
      matchingData?.skill_match?.missing_skills ||
      (suggestionsData?.suggestions?.find((s) => s.id === 'skills-target-role-alignment')?.issue?.match(/expected competencies:\s*([^.]+)/)?.[1]?.split(',').map((s) => s.trim())) ||
      [];

    const topPred = predictionData?.predictions?.[0];

    return {
      detected_skills: skillsList,
      top_predicted_domain: topPred?.category || null,
      top_prediction_confidence: topPred?.confidence || null,
      target_role: targetRole,
      missing_skills: missingSkills,
      roadmap_duration: roadmapData?.roadmap?.duration || null,
      readiness_score: suggestionsData?.readiness_score?.overall_score || null,
    };
  };

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoadingReply) return;

    setErrorMessage(null);
    setInputValue('');

    const newHistory = [...messages, { role: 'user', content: text }];
    setMessages(newHistory);
    setIsLoadingReply(true);

    try {
      const context = buildContextPayload();
      const payload = {
        message: text,
        conversation_history: messages.slice(-6),
        context,
        use_local_llm: useLocalLlm,
      };

      const res = await sendAssistantMessage(payload);
      setMessages([
        ...newHistory,
        {
          role: 'assistant',
          content: res.reply,
          engine: res.engine_used,
          followups: res.suggested_followups || [],
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to receive assistant reply.';
      setErrorMessage(detail);
    } finally {
      setIsLoadingReply(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const clearChat = () => {
    setMessages([]);
    setErrorMessage(null);
  };

  const contextData = buildContextPayload();
  const hasResumeLoaded = Boolean(analysisData?.filename);

  const starterPrompts = [
    'How should I tackle my top missing skills?',
    'Suggest a portfolio project using my current stack',
    'How do I rewrite resume bullets using the XYZ formula?',
    'Prepare me for entry-level technical interview questions',
    'Explain the difference between DistilBERT and Sentence-BERT scores',
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-fadeIn pb-8">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-start gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-600 text-white flex items-center justify-center shadow-sm shadow-indigo-500/20 shrink-0">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  AI Career Assistant
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Feature #5
                </span>
              </div>
              <p className="text-xs text-slate-500 max-w-xl leading-relaxed">
                Local, private career mentorship grounded in your verified resume skills, identified skill gaps, and roadmap milestones.
              </p>
            </div>
          </div>

          {/* Engine Status & Switcher */}
          <div className="flex flex-col sm:items-end gap-2 self-start sm:self-auto">
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border ${
                  ollamaStatus.ollama_available
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200/70'
                    : 'bg-indigo-50 text-indigo-700 border-indigo-200/70'
                }`}
              >
                {ollamaStatus.ollama_available ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Ollama ({ollamaStatus.configured_model})</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Guided Advisor (Instant CPU Mode)</span>
                  </>
                )}
              </span>

              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={clearChat}
                  title="Reset conversation"
                  className="p-1.5 rounded-xl border border-slate-200 text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Mode Toggle Checkbox */}
            {ollamaStatus.ollama_available && (
              <label className="flex items-center gap-1.5 text-[11px] text-slate-500 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useLocalLlm}
                  onChange={(e) => setUseLocalLlm(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span>Use Local Ollama LLM</span>
              </label>
            )}
          </div>
        </div>

        {/* Grounded Candidate Context Ribbon */}
        <div className="pt-4">
          <button
            type="button"
            onClick={() => setShowContextDetails(!showContextDetails)}
            className="w-full flex items-center justify-between text-xs text-slate-600 font-semibold hover:text-indigo-600 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>
                {hasResumeLoaded
                  ? `Grounded in active resume: ${analysisData.filename}`
                  : 'No resume loaded — running in general career advice mode'}
              </span>
              {contextData.target_role && (
                <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-bold">
                  Target: {contextData.target_role}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              <span>{showContextDetails ? 'Hide details' : 'View grounded profile data'}</span>
              {showContextDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {showContextDetails && (
            <div className="mt-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/70 text-xs space-y-2.5 animate-fadeIn">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-2.5 rounded-xl bg-white border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Verified Skills ({contextData.detected_skills.length})
                  </span>
                  <p className="text-slate-800 font-medium truncate">
                    {contextData.detected_skills.slice(0, 6).join(', ') || 'None loaded'}
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Target Role & Gaps
                  </span>
                  <p className="text-slate-800 font-medium truncate">
                    {contextData.target_role || 'Not selected'}
                    {contextData.missing_skills.length > 0 && ` • Gaps: ${contextData.missing_skills.slice(0, 3).join(', ')}`}
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Prediction & Readiness
                  </span>
                  <p className="text-slate-800 font-medium">
                    {contextData.top_predicted_domain || 'Pending'}
                    {contextData.readiness_score !== null && ` • Readiness: ${contextData.readiness_score}/100`}
                  </p>
                </div>
              </div>

              <p className="text-[10px] text-slate-400 italic">
                Privacy Protection: Personal contact details (email, phone, home address) are strictly filtered out and never grounded into prompts.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Stream Container */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-4 sm:p-6 shadow-sm min-h-[420px] flex flex-col justify-between">
        {/* Messages Stream */}
        <div className="space-y-4 mb-6 overflow-y-auto max-h-[560px] pr-1">
          {messages.length === 0 ? (
            /* Empty State / Welcome Screen */
            <div className="py-8 px-4 text-center max-w-lg mx-auto space-y-4">
              <div className="w-14 h-14 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-sm">
                <Sparkles className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  How can I guide your career today?
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  I can analyze your skill gaps, brainstorm production-level portfolio projects, polish resume bullets with the XYZ formula, and prep you for technical interviews.
                </p>
              </div>

              {/* Starter Prompt Chips */}
              <div className="pt-2 flex flex-col gap-2 text-left">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 text-center block mb-1">
                  Suggested Starters:
                </span>
                {starterPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 rounded-2xl bg-slate-50 hover:bg-indigo-50/60 border border-slate-200/80 text-xs font-medium text-slate-700 hover:text-indigo-900 transition-all text-left flex items-center justify-between group cursor-pointer"
                  >
                    <span>{prompt}</span>
                    <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 transition-colors shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Render Conversation Turns */
            messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold shadow-sm ${
                      isUser
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white'
                        : 'bg-slate-900 text-white'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`max-w-[85%] rounded-3xl p-4 sm:p-5 shadow-sm text-xs leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-tr-none'
                        : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-none'
                    }`}
                  >
                    {/* Assistant Metadata Header & Copy Button */}
                    {!isUser && (
                      <div className="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-200/60 text-[10px] text-slate-400">
                        <span className="font-semibold flex items-center gap-1">
                          {msg.engine?.includes('ollama') ? (
                            <>
                              <Cpu className="w-3 h-3 text-emerald-600" />
                              <span className="text-emerald-700 font-bold">Local Ollama LLM</span>
                            </>
                          ) : (
                            <>
                              <Zap className="w-3 h-3 text-indigo-600" />
                              <span className="text-indigo-700 font-bold">CareerAI Guided Advisor</span>
                            </>
                          )}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleCopy(msg.content, idx)}
                          className="flex items-center gap-1 text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
                        >
                          {copiedIndex === idx ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span className="text-emerald-600 font-bold">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}

                    {isUser ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <MarkdownText content={msg.content} />
                    )}

                    {/* Follow-up Prompts on Assistant turns */}
                    {!isUser && msg.followups && msg.followups.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200/60 space-y-1.5">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                          Suggested Next Steps:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.followups.map((f, fIdx) => (
                            <button
                              key={fIdx}
                              type="button"
                              onClick={() => handleSendMessage(f)}
                              className="px-2.5 py-1 rounded-lg bg-white hover:bg-indigo-50 border border-slate-200 text-[11px] font-medium text-slate-700 hover:text-indigo-900 transition-colors text-left cursor-pointer"
                            >
                              + {f}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Typing Indicator */}
          {isLoadingReply && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-3xl rounded-tl-none bg-slate-50 border border-slate-200/80 text-xs text-slate-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                <span>Generating grounded career advice...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-3 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">Assistant Error</p>
              <p className="text-rose-600">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="pt-3 border-t border-slate-100">
          <div className="relative flex items-center">
            <textarea
              rows={2}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about bridging skill gaps, capstone projects, XYZ resume bullets, or interview prep..."
              className="w-full resize-none p-3.5 pr-14 rounded-2xl border border-slate-200/80 bg-slate-50 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
            />
            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoadingReply}
              className="absolute right-3.5 w-8 h-8 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white flex items-center justify-center hover:from-indigo-500 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm active:scale-95 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2 px-1">
            <span>Press Enter to send, Shift + Enter for new line</span>
            <span>Mathematical ML scores cannot be altered by language models</span>
          </div>
        </div>
      </div>
    </div>
  );
}
