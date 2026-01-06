/**
 * API Client for Survey Backend
 */
class SurveyAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        try {
            log('API Request:', options.method || 'GET', endpoint);
            
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            log('API Response:', data);
            
            return data;
        } catch (error) {
            log('API Error:', error);
            throw error;
        }
    }

    // Session endpoints
    async startSession(surveyId, respondentId = null) {
        return this.request('/sessions/start', {
            method: 'POST',
            body: JSON.stringify({
                survey_id: surveyId,
                respondent_id: respondentId,
                anonymous_id: respondentId
            })
        });
    }

    async submitAnswer(sessionId, answer) {
        return this.request(`/sessions/${sessionId}/answer`, {
            method: 'POST',
            body: JSON.stringify(answer)
        });
    }

    async endSession(sessionId, reason = 'user_requested') {
        return this.request(`/sessions/${sessionId}/end`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    // Admin endpoints
    async listSessions(status = null, limit = 50, offset = 0) {
        let endpoint = `/admin/sessions?limit=${limit}&offset=${offset}`;
        if (status) {
            endpoint += `&status=${status}`;
        }
        return this.request(endpoint);
    }

    async getSessionDetail(sessionId) {
        return this.request(`/admin/sessions/${sessionId}`);
    }

    async exportSessions(format = 'json') {
        const url = `${this.baseUrl}/export/sessions.${format}`;
        window.open(url, '_blank');
    }
}

// Create global API instance
const api = new SurveyAPI(CONFIG.API_BASE_URL);