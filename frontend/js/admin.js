/**
 * Admin Dashboard Logic
 */
class AdminApp {
    constructor() {
        this.sessions = [];
        this.currentView = 'list';
        this.selectedSessionId = null;
        
        this.init();
    }

    async init() {
        await this.loadSessions();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });

        // Export buttons
        document.getElementById('export-json-btn')?.addEventListener('click', () => {
            api.exportSessions('json');
        });

        document.getElementById('export-csv-btn')?.addEventListener('click', () => {
            api.exportSessions('csv');
        });

        // Refresh button
        document.getElementById('refresh-btn')?.addEventListener('click', () => {
            this.loadSessions();
        });
    }

    switchView(view) {
        this.currentView = view;
        
        // Update tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.view === view) {
                tab.classList.add('active');
            }
        });
        
        // Update content
        if (view === 'list') {
            this.renderSessionsList();
        }
    }

    async loadSessions() {
        try {
            this.showLoading();
            
            this.sessions = await api.listSessions();
            
            this.hideLoading();
            this.renderSessionsList();
            
        } catch (error) {
            this.showError('Failed to load sessions: ' + error.message);
        }
    }

    renderSessionsList() {
        const container = document.getElementById('content');
        
        if (this.sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <h3>No Sessions Yet</h3>
                    <p>Sessions will appear here once respondents start taking surveys.</p>
                </div>
            `;
            return;
        }
        
        const tableHtml = `
            <div class="card">
                <table class="sessions-table">
                    <thead>
                        <tr>
                            <th>Session ID</th>
                            <th>Survey</th>
                            <th>Status</th>
                            <th>Started</th>
                            <th>Messages</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.sessions.map(session => this.renderSessionRow(session)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHtml;
        
        // Attach event listeners for view buttons
        document.querySelectorAll('.view-session-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sessionId = e.target.dataset.sessionId;
                this.viewSessionDetail(sessionId);
            });
        });
    }

    renderSessionRow(session) {
        const statusClass = `status-${session.status}`;
        const startedAt = new Date(session.started_at).toLocaleString();
        
        return `
            <tr>
                <td><code>${session.session_id.substr(0, 8)}...</code></td>
                <td>${this.escapeHtml(session.survey_name)}</td>
                <td>
                    <span class="status-badge ${statusClass}">${session.status}</span>
                </td>
                <td>${startedAt}</td>
                <td>${session.message_count}</td>
                <td>
                    <button 
                        class="btn-primary view-session-btn" 
                        data-session-id="${session.session_id}"
                        style="padding: 8px 16px; font-size: 0.875rem;"
                    >
                        View Details
                    </button>
                </td>
            </tr>
        `;
    }

    async viewSessionDetail(sessionId) {
        try {
            this.showLoading();
            
            const detail = await api.getSessionDetail(sessionId);
            
            this.hideLoading();
            this.renderSessionDetail(detail);
            
        } catch (error) {
            this.showError('Failed to load session detail: ' + error.message);
        }
    }

    renderSessionDetail(detail) {
        const container = document.getElementById('content');
        
        const startedAt = new Date(detail.started_at).toLocaleString();
        const completedAt = detail.completed_at 
            ? new Date(detail.completed_at).toLocaleString()
            : 'N/A';
        
        container.innerHTML = `
            <div class="session-detail-header">
                <div>
                    <h2>Session Details</h2>
                    <p><code>${detail.session_id}</code></p>
                </div>
                <button onclick="adminApp.loadSessions()" class="btn-secondary">
                    ← Back to List
                </button>
            </div>
            
            <div class="card">
                <h3>Overview</h3>
                <div class="session-meta">
                    <div class="meta-item">
                        <div class="meta-label">AI Calls</div>
                        <div class="meta-value">${detail.llm_calls_count}</div>
                            <span class="status-badge status-${detail.status}">${detail.status}</span>
                        </div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Survey</div>
                        <div class="meta-value" style="font-size: 1rem;">${this.escapeHtml(detail.survey_name)}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Started</div>
                        <div class="meta-value" style="font-size: 0.9rem;">${startedAt}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Completed</div>
                        <div class="meta-value" style="font-size: 0.9rem;">${completedAt}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Total Messages</div>
                        <div class="meta-value">${detail.messages.length}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">AI Calls</div>
                        <div class="meta-value">${detail.model_calls_count}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Tokens Used</div>
                        <div class="meta-value">${detail.total_tokens.toLocaleString()}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Cost</div>
                        <div class="meta-value">$${detail.total_cost_usd.toFixed(4)}</div>
                    </div>
                </div>
            </div>
            
            ${detail.summary ? `
                <div class="card">
                    <h3>Summary</h3>
                    <p>${this.escapeHtml(detail.summary)}</p>
                    ${detail.key_themes && detail.key_themes.length > 0 ? `
                        <div class="mt-2">
                            <strong>Key Themes:</strong>
                            ${detail.key_themes.map(theme => 
                                `<span class="badge badge-primary">${this.escapeHtml(theme)}</span>`
                            ).join(' ')}
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            <div class="card">
                <h3>Conversation Transcript</h3>
                <div class="messages-timeline">
                    ${detail.messages.map(msg => this.renderMessage(msg)).join('')}
                </div>
            </div>
        `;
    }

    renderMessage(message) {
        const messageClass = message.is_follow_up ? 'message-followup' : 
                             message.message_type.includes('user') ? 'message-user' : '';
        
        const typeLabels = {
            'survey_question': '📝 Survey Question',
            'user_answer': '💬 User Answer',
            'follow_up_question': '🤔 Follow-up Question',
            'follow_up_answer': '💭 Follow-up Answer',
            'prefer_not_to_answer': '🚫 Prefer Not To Answer'
        };
        
        const typeLabel = typeLabels[message.message_type] || message.message_type;
        
        return `
            <div class="message-item ${messageClass}">
                <div class="message-type">${typeLabel}</div>
                <div class="message-text">${this.escapeHtml(message.message_text)}</div>
                ${message.followup_reason ? `
                    <div class="mt-1" style="font-size: 0.875rem; color: var(--text-secondary);">
                        <em>Reason: ${this.escapeHtml(message.followup_reason)}</em>
                    </div>
                ` : ''}
            </div>
        `;
    }

    showLoading() {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner" style="border-color: var(--primary-color); border-top-color: transparent; width: 40px; height: 40px;"></div>
                <p class="mt-2">Loading...</p>
            </div>
        `;
    }

    hideLoading() {
        // Loading is replaced by content
    }

    showError(message) {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="alert alert-error">
                <strong>Error:</strong> ${this.escapeHtml(message)}
            </div>
        `;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
let adminApp;
document.addEventListener('DOMContentLoaded', () => {
    adminApp = new AdminApp();
});