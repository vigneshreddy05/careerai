import axios from 'axios';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'https://careerai-api-xheu.onrender.com/api'
).replace(/\/$/, '');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
});

// Attach Authorization header if JWT token is stored in localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('careerai_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global response interceptor for error handling, token expiration, and toasts
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined') {
      if (error.response) {
        const { status, data } = error.response;

        if (status === 401) {
          const hadToken = localStorage.getItem('careerai_token');
          if (hadToken) {
            localStorage.removeItem('careerai_token');
            window.dispatchEvent(
              new CustomEvent('careerai:toast', {
                detail: {
                  message: 'Your session has expired. Please log in again.',
                  type: 'warning',
                },
              })
            );
          }
        } else if (status === 429) {
          window.dispatchEvent(
            new CustomEvent('careerai:toast', {
              detail: {
                message: data?.detail || 'Rate limit exceeded. Please wait a moment before retrying.',
                type: 'warning',
              },
            })
          );
        } else if (status === 500) {
          window.dispatchEvent(
            new CustomEvent('careerai:toast', {
              detail: {
                message: data?.detail || 'An unexpected server error occurred. Please try again later.',
                type: 'error',
              },
            })
          );
        }
      } else if (error.request && !window.navigator.onLine) {
        window.dispatchEvent(
          new CustomEvent('careerai:toast', {
            detail: {
              message: 'You appear to be offline. Please check your network connection.',
              type: 'error',
            },
          })
        );
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Register a new user account.
 * @param {Object} userData - Registration payload
 * @returns {Promise<Object>} { success, token, user }
 */
export async function registerUser(userData) {
  const response = await apiClient.post('/auth/register', userData);
  return response.data;
}

/**
 * Authenticate an existing user.
 * @param {Object} credentials - { email, password }
 * @returns {Promise<Object>} { success, token, user }
 */
export async function loginUser(credentials) {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
}

/**
 * Invalidate current session token.
 * @returns {Promise<Object>} { success, message }
 */
export async function logoutUser() {
  const response = await apiClient.post('/auth/logout');
  return response.data;
}

/**
 * Fetch current authenticated user's profile.
 * @returns {Promise<Object>} { success, user }
 */
export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me');
  return response.data;
}

/**
 * Update candidate profile and privacy settings.
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} { success, user }
 */
export async function updateUserProfile(updates) {
  const response = await apiClient.put('/auth/profile', updates);
  return response.data;
}

/**
 * Permanently delete authenticated user's account and data.
 * @returns {Promise<Object>} { success, message }
 */
export async function deleteUserAccount() {
  const response = await apiClient.delete('/auth/account');
  return response.data;
}

/**
 * Persist or sync an analysis session snapshot for the authenticated user.
 * @param {Object} payload - History snapshot payload
 * @returns {Promise<Object>} { success, record_id, message }
 */
export async function saveHistorySnapshot(payload) {
  const response = await apiClient.post('/history/save', payload);
  return response.data;
}

/**
 * List all saved analysis history records for current authenticated user.
 * @returns {Promise<Object>} { success, records, total }
 */
export async function getHistoryList() {
  const response = await apiClient.get('/history');
  return response.data;
}

/**
 * Retrieve aggregated analytics and progression metrics across user's history.
 * @returns {Promise<Object>} History analytics response
 */
export async function getHistoryAnalytics() {
  const response = await apiClient.get('/history/analytics');
  return response.data;
}

/**
 * Retrieve full historical detail and snapshot by record ID.
 * @param {string} recordId - History record UUID
 * @returns {Promise<Object>} { success, record }
 */
export async function getHistoryDetail(recordId) {
  const response = await apiClient.get(`/history/${recordId}`);
  return response.data;
}

/**
 * Delete a single historical analysis record.
 * @param {string} recordId - History record UUID
 * @returns {Promise<Object>} { success, message }
 */
export async function deleteHistoryItem(recordId) {
  const response = await apiClient.delete(`/history/${recordId}`);
  return response.data;
}

/**
 * Clear all historical analysis records for authenticated user.
 * @returns {Promise<Object>} { success, message, deleted_count }
 */
export async function clearAllHistory() {
  const response = await apiClient.delete('/history');
  return response.data;
}

/**
 * Upload and analyze a resume file (PDF or DOCX).
 * @param {File} file - The resume file object
 * @param {Function} [onUploadProgress] - Optional progress callback
 * @returns {Promise<Object>} Backend analysis response
 */
export async function analyzeResume(file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/resume/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });

  return response.data;
}

/**
 * Request job-role prediction from extracted resume text using fine-tuned DistilBERT.
 * @param {string} resumeText - Extracted text from the analyzed resume
 * @returns {Promise<Object>} Prediction response with top 3 categories and confidence scores
 */
export async function predictJobRole(resumeText) {
  const response = await apiClient.post('/predictions/job-role', {
    resume_text: resumeText,
  });
  return response.data;
}

/**
 * Match candidate resume text against a target job description using Sentence-BERT and skill gap extraction.
 * @param {string} resumeText - Extracted text from the analyzed resume
 * @param {string} jobDescription - Target job posting or description text
 * @param {string} [jobTitle] - Optional title or role label
 * @returns {Promise<Object>} Matching response with semantic score, skill breakdown, and suggestions
 */
export async function matchResumeToJobDescription(resumeText, jobDescription, jobTitle = null) {
  const response = await apiClient.post('/match/job-description', {
    resume_text: resumeText,
    job_description: jobDescription,
    job_title: jobTitle,
  });
  return response.data;
}

/**
 * Generate personalized career role recommendations based on candidate profile.
 * @param {Object} payload - { resume_skills, predicted_categories, experience_years }
 * @returns {Promise<Object>} Career recommendations response with strong matches and alternative paths
 */
export async function getCareerRecommendations(payload) {
  const response = await apiClient.post('/roadmap/recommendations', payload);
  return response.data;
}

/**
 * Generate personalized 30-day or 60-day learning roadmap with weekly milestones.
 * @param {Object} payload - { target_role, resume_skills, duration, custom_missing_skills }
 * @returns {Promise<Object>} Roadmap response with milestones, deliverables, and verified resources
 */
export async function generateRoadmap(payload) {
  const response = await apiClient.post('/roadmap/generate', payload);
  return response.data;
}

/**
 * Retrieve list of benchmark career roles.
 * @returns {Promise<Array<string>>} List of role titles
 */
export async function getAvailableRoles() {
  const response = await apiClient.get('/roadmap/available-roles');
  return response.data;
}

/**
 * Generate structural completeness score and prioritized resume improvement suggestions.
 * @param {Object} payload - { filename, contact_info, skills, education, experience, projects, statistics, extracted_text, target_role, custom_missing_skills }
 * @returns {Promise<Object>} Suggestions response with readiness breakdown and prioritized items
 */
export async function getResumeSuggestions(payload) {
  const response = await apiClient.post('/suggestions/analyze', payload);
  return response.data;
}

/**
 * Check local Ollama health status and model availability.
 * @returns {Promise<Object>} { ollama_available, ollama_base_url, configured_model, available_models, status }
 */
export async function getAssistantStatus() {
  const response = await apiClient.get('/assistant/status');
  return response.data;
}

/**
 * Send conversational message to Career Assistant with grounded profile context.
 * @param {Object} payload - { message, conversation_history, context, use_local_llm }
 * @returns {Promise<Object>} { success, reply, engine_used, ollama_available, suggested_followups, disclaimer }
 */
export async function sendAssistantMessage(payload) {
  const response = await apiClient.post('/assistant/chat', payload);
  return response.data;
}

/**
 * Retrieve list of all uploaded resume submissions and registered users (Protected).
 * @param {string} adminKey - Admin access secret key
 * @param {number} limit - Maximum number of items to retrieve
 * @returns {Promise<Object>} { total_submissions, submissions, total_users, users }
 */
export async function getAdminSubmissions(adminKey, limit = 200) {
  const response = await apiClient.get('/admin/submissions', {
    params: { limit },
    headers: { 'X-Admin-Key': adminKey },
  });
  return response.data;
}

/**
 * Retrieve complete details of a single resume submission including full extracted text (Protected).
 * @param {string} adminKey - Admin access secret key
 * @param {string} submissionId - ID of submission to retrieve
 * @returns {Promise<Object>} { success, submission }
 */
export async function getAdminSubmissionDetail(adminKey, submissionId) {
  const response = await apiClient.get(`/admin/submissions/${submissionId}`, {
    headers: { 'X-Admin-Key': adminKey },
  });
  return response.data;
}

/**
 * Permanently delete a resume submission record (Protected).
 * @param {string} adminKey - Admin access secret key
 * @param {string} submissionId - ID of submission to delete
 * @returns {Promise<Object>} { success, message }
 */
export async function deleteAdminSubmission(adminKey, submissionId) {
  const response = await apiClient.delete(`/admin/submissions/${submissionId}`, {
    headers: { 'X-Admin-Key': adminKey },
  });
  return response.data;
}

export default apiClient;
