import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import {
  analyzeResume,
  predictJobRole,
  matchResumeToJobDescription,
  getCareerRecommendations,
  generateRoadmap,
  getResumeSuggestions,
  saveHistorySnapshot,
  getHistoryDetail,
} from '../services/api';

const ResumeContext = createContext(null);

export function ResumeProvider({ children }) {
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Job Prediction state
  const [predictionData, setPredictionData] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState(null);

  // Semantic Job Description Matching state
  const [matchingData, setMatchingData] = useState(null);
  const [isMatching, setIsMatching] = useState(false);
  const [matchingError, setMatchingError] = useState(null);

  // Career Recommendations state
  const [recommendationsData, setRecommendationsData] = useState(null);
  const [isRecommending, setIsRecommending] = useState(false);
  const [recommendationsError, setRecommendationsError] = useState(null);

  // Personalized Roadmap state
  const [roadmapData, setRoadmapData] = useState(null);
  const [isGeneratingRoadmap, setIsGeneratingRoadmap] = useState(false);
  const [roadmapError, setRoadmapError] = useState(null);
  const [selectedTargetRole, setSelectedTargetRole] = useState(null);

  // Resume Improvement Suggestions state
  const [suggestionsData, setSuggestionsData] = useState(null);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState(null);

  // Stable refs for mutable state accessed inside callbacks
  const analysisDataRef = useRef(analysisData);
  const predictionDataRef = useRef(predictionData);
  const matchingDataRef = useRef(matchingData);
  const selectedTargetRoleRef = useRef(selectedTargetRole);
  const suggestionsDataRef = useRef(suggestionsData);

  useEffect(() => {
    analysisDataRef.current = analysisData;
  }, [analysisData]);

  useEffect(() => {
    predictionDataRef.current = predictionData;
  }, [predictionData]);

  useEffect(() => {
    matchingDataRef.current = matchingData;
  }, [matchingData]);

  useEffect(() => {
    selectedTargetRoleRef.current = selectedTargetRole;
  }, [selectedTargetRole]);

  useEffect(() => {
    suggestionsDataRef.current = suggestionsData;
  }, [suggestionsData]);

  // Suggestions in-memory cache and in-flight guard
  const suggestionsCacheRef = useRef({});
  const activeSuggestionsKeyRef = useRef(null);

  // Roadmap in-memory cache and in-flight request guards
  const roadmapCacheRef = useRef({});
  const activeRoadmapKeyRef = useRef(null);
  const roadmapRequestSeqRef = useRef(0);

  // Recommendations cache and in-flight request guard
  const recommendationsCacheRef = useRef({});
  const activeRecommendationsKeyRef = useRef(null);

  // Active persistent history record reference (for authenticated users)
  const activeHistoryRecordIdRef = useRef(null);

  const syncHistorySession = useCallback(async (overrides = {}) => {
    const token = localStorage.getItem('careerai_token');
    if (!token) return; // Guest mode: silently skip persistence

    const currentAnalysis = overrides.analysisData || analysisDataRef.current;
    if (!currentAnalysis || !currentAnalysis.filename) return;

    const currentPred = overrides.predictionData !== undefined ? overrides.predictionData : predictionDataRef.current;
    const currentMatch = overrides.matchingData !== undefined ? overrides.matchingData : matchingDataRef.current;
    const currentRoadmap = overrides.roadmapData !== undefined ? overrides.roadmapData : roadmapDataRef.current;
    const currentRecs = overrides.recommendationsData !== undefined ? overrides.recommendationsData : recommendationsDataRef.current;
    const currentRole = overrides.selectedTargetRole !== undefined ? overrides.selectedTargetRole : selectedTargetRoleRef.current;
    const currentSugg = overrides.suggestionsData !== undefined ? overrides.suggestionsData : suggestionsDataRef.current;

    const payload = {
      record_id: activeHistoryRecordIdRef.current,
      filename: currentAnalysis.filename,
      skills: currentAnalysis.skills || {},
      education_summary: currentAnalysis.education?.[0]?.degree || null,
      experience_years: currentAnalysis.experience?.total_years_estimated || null,
      top_prediction: currentPred || null,
      latest_match: currentMatch ? {
        job_title: currentMatch.job_title,
        semantic_score: currentMatch.semantic_match?.similarity_score,
        match_percentage: currentMatch.skill_match?.match_percentage,
        matching_skills: currentMatch.skill_match?.matching_skills,
        missing_skills: currentMatch.skill_match?.missing_skills,
      } : null,
      latest_roadmap: currentRoadmap?.roadmap ? {
        target_role: currentRoadmap.roadmap.role_title,
        duration: currentRoadmap.roadmap.duration,
        target_level: currentRoadmap.roadmap.target_level,
      } : null,
      extracted_text: currentAnalysis.extracted_text || currentAnalysis.text_preview || null,
      full_snapshot: {
        analysisData: currentAnalysis,
        predictionData: currentPred,
        matchingData: currentMatch,
        recommendationsData: currentRecs,
        roadmapData: currentRoadmap,
        selectedTargetRole: currentRole,
        suggestionsData: currentSugg,
      },
    };

    try {
      const res = await saveHistorySnapshot(payload);
      if (res && res.record_id) {
        activeHistoryRecordIdRef.current = res.record_id;
      }
    } catch (err) {
      console.warn('History auto-sync notice:', err.message);
    }
  }, []);

  const loadHistoryRecord = useCallback(async (recordId) => {
    const detail = await getHistoryDetail(recordId);
    if (!detail || !detail.record) {
      throw new Error('Could not find requested history record.');
    }

    const rec = detail.record;
    activeHistoryRecordIdRef.current = rec.id;

    // Reset caches so new record data is freshly represented
    roadmapCacheRef.current = {};
    activeRoadmapKeyRef.current = null;
    recommendationsCacheRef.current = {};
    activeRecommendationsKeyRef.current = null;
    suggestionsCacheRef.current = {};
    activeSuggestionsKeyRef.current = null;

    if (rec.full_snapshot) {
      const snap = rec.full_snapshot;
      if (snap.analysisData) setAnalysisData(snap.analysisData);
      if (snap.predictionData) setPredictionData(snap.predictionData);
      if (snap.matchingData) setMatchingData(snap.matchingData);
      if (snap.recommendationsData) setRecommendationsData(snap.recommendationsData);
      if (snap.roadmapData) setRoadmapData(snap.roadmapData);
      if (snap.selectedTargetRole) setSelectedTargetRole(snap.selectedTargetRole);
      if (snap.suggestionsData) setSuggestionsData(snap.suggestionsData);
    } else {
      // Reconstruct minimal analysisData from stored fields
      setAnalysisData({
        success: true,
        filename: rec.filename,
        file_type: rec.filename.endsWith('.pdf') ? 'application/pdf' : 'application/docx',
        skills: rec.skills || { all_skills: [] },
        education: rec.education_summary ? [{ degree: rec.education_summary }] : [],
        experience: { total_years_estimated: rec.experience_years, entries: [] },
        projects: [],
        statistics: {
          word_count: 0,
          character_count: 0,
          skill_count: rec.skills?.all_skills?.length || 0,
          education_count: 0,
          experience_count: 0,
          project_count: 0,
        },
        text_preview: rec.extracted_text ? rec.extracted_text.slice(0, 300) : '',
        extracted_text: rec.extracted_text,
      });
      if (rec.top_prediction) setPredictionData(rec.top_prediction);
      if (rec.latest_match) setMatchingData(rec.latest_match);
      if (rec.latest_roadmap) setRoadmapData({ roadmap: rec.latest_roadmap });
    }
    return rec;
  }, []);

  const uploadFile = useCallback(async (file) => {
    if (!file) {
      setError('Please select a file to upload.');
      return null;
    }

    // Client-side pre-validation
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.pdf') && !lowerName.endsWith('.docx')) {
      setError('Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).');
      return null;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('File exceeds maximum allowed size of 5 MB.');
      return null;
    }

    setIsLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const data = await analyzeResume(file, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        }
      });

      // Clear all cached roadmap, recommendations & suggestions data on new file upload
      roadmapCacheRef.current = {};
      activeRoadmapKeyRef.current = null;
      recommendationsCacheRef.current = {};
      activeRecommendationsKeyRef.current = null;
      suggestionsCacheRef.current = {};
      activeSuggestionsKeyRef.current = null;
      activeHistoryRecordIdRef.current = null;

      setAnalysisData(data);
      setPredictionData(null);
      setPredictionError(null);
      setMatchingData(null);
      setMatchingError(null);
      setRecommendationsData(null);
      setRecommendationsError(null);
      setRoadmapData(null);
      setRoadmapError(null);
      setSuggestionsData(null);
      setSuggestionsError(null);
      setSelectedTargetRole(null);
      setIsLoading(false);
      setUploadProgress(100);

      // Persist / sync active session to history for authenticated users
      syncHistorySession({ analysisData: data, predictionData: null, matchingData: null, roadmapData: null, suggestionsData: null });

      return data;
    } catch (err) {
      let message = 'An error occurred while analyzing the resume.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setError(message);
      setIsLoading(false);
      setUploadProgress(0);
      throw new Error(message);
    }
  }, []);

  const fetchJobPrediction = useCallback(async (customText = null) => {
    const currentAnalysis = analysisDataRef.current;
    const textToUse = customText || currentAnalysis?.extracted_text || currentAnalysis?.text_preview;

    if (!textToUse || !textToUse.trim()) {
      setPredictionError('No extracted resume text available. Please upload and analyze a resume first.');
      return null;
    }

    setIsPredicting(true);
    setPredictionError(null);

    try {
      const result = await predictJobRole(textToUse);
      setPredictionData(result);
      syncHistorySession({ predictionData: result });
      return result;
    } catch (err) {
      let message = 'An error occurred while predicting job role.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setPredictionError(message);
      throw new Error(message);
    } finally {
      setIsPredicting(false);
    }
  }, []);

  const executeJobMatch = useCallback(async (jobDescription, jobTitle = null, customResumeText = null) => {
    const currentAnalysis = analysisDataRef.current;
    const resumeTextToUse = customResumeText || currentAnalysis?.extracted_text || currentAnalysis?.text_preview;

    if (!resumeTextToUse || !resumeTextToUse.trim()) {
      setMatchingError('No extracted resume text available. Please upload and analyze a resume first.');
      return null;
    }

    if (!jobDescription || !jobDescription.trim()) {
      setMatchingError('Please provide a job description to compare against.');
      return null;
    }

    setIsMatching(true);
    setMatchingError(null);

    try {
      const result = await matchResumeToJobDescription(resumeTextToUse, jobDescription, jobTitle);
      setMatchingData(result);
      syncHistorySession({ matchingData: result });
      return result;
    } catch (err) {
      let message = 'An error occurred while matching resume to job description.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setMatchingError(message);
      throw new Error(message);
    } finally {
      setIsMatching(false);
    }
  }, []);

  const fetchRecommendations = useCallback(async (forceRefresh = false) => {
    const currentAnalysis = analysisDataRef.current;
    if (!currentAnalysis) {
      setRecommendationsError('Please upload and analyze a resume first.');
      return null;
    }

    const skills = currentAnalysis.skills?.all_skills || [];
    const currentPred = predictionDataRef.current;
    const categories = currentPred?.predictions?.map((p) => p.category) || [];
    const expYears = currentAnalysis.experience?.total_years_estimated || null;
    const cacheKey = `${currentAnalysis.filename || 'resume'}|${skills.join(',')}|${categories.join(',')}|${expYears}`;

    if (!forceRefresh && recommendationsCacheRef.current[cacheKey]) {
      const cached = recommendationsCacheRef.current[cacheKey];
      setRecommendationsData(cached);
      setRecommendationsError(null);
      setIsRecommending(false);
      return cached;
    }

    if (activeRecommendationsKeyRef.current === cacheKey) {
      return null;
    }
    activeRecommendationsKeyRef.current = cacheKey;

    setIsRecommending(true);
    setRecommendationsError(null);

    try {
      const result = await getCareerRecommendations({
        resume_skills: skills,
        predicted_categories: categories,
        experience_years: expYears,
      });

      recommendationsCacheRef.current[cacheKey] = result;
      setRecommendationsData(result);
      setRecommendationsError(null);
      return result;
    } catch (err) {
      let message = 'An error occurred while generating career recommendations.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setRecommendationsError(message);
      throw new Error(message);
    } finally {
      activeRecommendationsKeyRef.current = null;
      setIsRecommending(false);
    }
  }, []);

  const fetchRoadmap = useCallback(
    async (targetRole, duration = '30-day', customMissingSkills = null, forceRefresh = false) => {
      const currentAnalysis = analysisDataRef.current;
      if (!currentAnalysis) {
        setRoadmapError('Please upload and analyze a resume first.');
        return null;
      }

      const roleToUse = targetRole || selectedTargetRoleRef.current || 'Full Stack Software Engineer';
      const durationToUse = duration === '60-day' ? '60-day' : '30-day';
      const skills = currentAnalysis.skills?.all_skills || [];
      const missingKey =
        customMissingSkills && Array.isArray(customMissingSkills)
          ? [...customMissingSkills].sort().join(',')
          : '';
      const skillsKey = [...skills].sort().join(',');
      const cacheKey = `${currentAnalysis.filename || 'resume'}|${roleToUse}|${durationToUse}|${skillsKey}|${missingKey}`;

      // 1. Return from in-memory cache if available and not forced
      if (!forceRefresh && roadmapCacheRef.current[cacheKey]) {
        const cached = roadmapCacheRef.current[cacheKey];
        setRoadmapData(cached);
        setRoadmapError(null);
        setIsGeneratingRoadmap(false);
        return cached;
      }

      // 2. Prevent duplicate simultaneous in-flight requests for identical parameters
      if (activeRoadmapKeyRef.current === cacheKey) {
        return null;
      }

      activeRoadmapKeyRef.current = cacheKey;
      const currentSeq = ++roadmapRequestSeqRef.current;

      setIsGeneratingRoadmap(true);
      setRoadmapError(null);

      try {
        const result = await generateRoadmap({
          target_role: roleToUse,
          resume_skills: skills,
          duration: durationToUse,
          custom_missing_skills: customMissingSkills,
        });

        // Ensure we only commit state if this request is still the latest one in sequence
        if (currentSeq === roadmapRequestSeqRef.current) {
          roadmapCacheRef.current[cacheKey] = result;
          setRoadmapData(result);
          setRoadmapError(null);
          syncHistorySession({ roadmapData: result });
        }
        return result;
      } catch (err) {
        if (currentSeq === roadmapRequestSeqRef.current) {
          let message = 'An error occurred while generating learning roadmap.';
          if (err.response && err.response.data && err.response.data.detail) {
            message = err.response.data.detail;
          } else if (err.message) {
            message = err.message;
          }
          setRoadmapError(message);
        }
        throw err;
      } finally {
        if (activeRoadmapKeyRef.current === cacheKey) {
          activeRoadmapKeyRef.current = null;
        }
        if (currentSeq === roadmapRequestSeqRef.current) {
          setIsGeneratingRoadmap(false);
        }
      }
    },
    []
  );

  const fetchResumeSuggestions = useCallback(
    async (targetRole = null, customMissingSkills = [], forceRefresh = false) => {
      const currentAnalysis = analysisDataRef.current;
      if (!currentAnalysis) {
        setSuggestionsError('No analyzed resume available. Please upload a resume first.');
        return null;
      }

      const roleKey = (targetRole || 'general').trim().toLowerCase();
      const cacheKey = `${currentAnalysis.filename || 'resume'}_${roleKey}`;

      if (!forceRefresh && suggestionsCacheRef.current[cacheKey]) {
        const cached = suggestionsCacheRef.current[cacheKey];
        setSuggestionsData(cached);
        setSuggestionsError(null);
        setIsLoadingSuggestions(false);
        return cached;
      }

      if (activeSuggestionsKeyRef.current === cacheKey) {
        return null;
      }

      activeSuggestionsKeyRef.current = cacheKey;
      setIsLoadingSuggestions(true);
      setSuggestionsError(null);

      try {
        const payload = {
          filename: currentAnalysis.filename,
          contact_info: currentAnalysis.contact_info,
          skills: currentAnalysis.skills,
          education: currentAnalysis.education,
          experience: currentAnalysis.experience,
          projects: currentAnalysis.projects,
          statistics: currentAnalysis.statistics,
          extracted_text: currentAnalysis.extracted_text || currentAnalysis.text_preview,
          target_role: targetRole,
          custom_missing_skills: customMissingSkills,
        };

        const response = await getResumeSuggestions(payload);
        suggestionsCacheRef.current[cacheKey] = response;
        setSuggestionsData(response);
        setSuggestionsError(null);
        syncHistorySession({ suggestionsData: response });
        return response;
      } catch (err) {
        let message = 'An error occurred while generating resume suggestions.';
        if (err.response && err.response.data && err.response.data.detail) {
          message = err.response.data.detail;
        } else if (err.message) {
          message = err.message;
        }
        setSuggestionsError(message);
        throw new Error(message);
      } finally {
        if (activeSuggestionsKeyRef.current === cacheKey) {
          activeSuggestionsKeyRef.current = null;
        }
        setIsLoadingSuggestions(false);
      }
    },
    [syncHistorySession]
  );

  const clearAnalysis = useCallback(() => {
    roadmapCacheRef.current = {};
    activeRoadmapKeyRef.current = null;
    recommendationsCacheRef.current = {};
    activeRecommendationsKeyRef.current = null;
    suggestionsCacheRef.current = {};
    activeSuggestionsKeyRef.current = null;
    activeHistoryRecordIdRef.current = null;

    setAnalysisData(null);
    setError(null);
    setIsLoading(false);
    setUploadProgress(0);
    setPredictionData(null);
    setPredictionError(null);
    setIsPredicting(false);
    setMatchingData(null);
    setMatchingError(null);
    setIsMatching(false);
    setRecommendationsData(null);
    setRecommendationsError(null);
    setIsRecommending(false);
    setRoadmapData(null);
    setRoadmapError(null);
    setIsGeneratingRoadmap(false);
    setSuggestionsData(null);
    setSuggestionsError(null);
    setIsLoadingSuggestions(false);
    setSelectedTargetRole(null);
  }, []);

  return (
    <ResumeContext.Provider
      value={{
        analysisData,
        isLoading,
        error,
        uploadProgress,
        uploadFile,
        clearAnalysis,
        setError,
        predictionData,
        isPredicting,
        predictionError,
        fetchJobPrediction,
        setPredictionError,
        matchingData,
        isMatching,
        matchingError,
        executeJobMatch,
        setMatchingError,
        setMatchingData,
        recommendationsData,
        isRecommending,
        recommendationsError,
        fetchRecommendations,
        setRecommendationsError,
        roadmapData,
        isGeneratingRoadmap,
        roadmapError,
        fetchRoadmap,
        setRoadmapError,
        selectedTargetRole,
        setSelectedTargetRole,
        setRoadmapData,
        suggestionsData,
        isLoadingSuggestions,
        suggestionsError,
        fetchResumeSuggestions,
        setSuggestionsData,
        setSuggestionsError,
        loadHistoryRecord,
      }}
    >
      {children}
    </ResumeContext.Provider>
  );
}

export function useResume() {
  const context = useContext(ResumeContext);
  if (!context) {
    throw new Error('useResume must be used within a ResumeProvider');
  }
  return context;
}
