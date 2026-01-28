// ===============================
// Respondent ID helpers
// ===============================

/**
 * Generate a unique respondent ID
 */
function generateRespondentId() {
    return "resp_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
}

/**
 * Get or create respondent ID from localStorage.
 * Persists across refreshes in the same browser.
 */
function getOrCreateRespondentId() {
    const STORAGE_KEY = "polling_survey_respondent_id";
    let respondentId = localStorage.getItem(STORAGE_KEY);

    if (!respondentId) {
        respondentId = generateRespondentId();
        localStorage.setItem(STORAGE_KEY, respondentId);
        console.log("Created new respondent ID:", respondentId);
    } else {
        console.log("Using existing respondent ID:", respondentId);
    }

    return respondentId;
}

/**
 * Optional: Clear respondent ID (for testing)
 */
function clearRespondentId() {
    localStorage.removeItem("polling_survey_respondent_id");
    console.log("Cleared respondent ID");
}

/**
 * Display respondent ID using your HTML block:
 *  <div id="respondent-info"> ... <span id="respondent-id-value"></span>
 */
function displayRespondentId(respondentId) {
    const wrapper = document.getElementById("respondent-info");
    const value = document.getElementById("respondent-id-value");

    if (wrapper && value) {
        value.textContent = respondentId;
        wrapper.style.display = "block";
    }
}


// ===============================
// Survey Application Logic
// ===============================
class SurveyApp {
    constructor() {
        this.sessionId = null;
        this.currentQuestion = null;
        this.totalQuestions = 0;
        this.currentPosition = 0;
        this.isFollowUp = false;
        this.isLoading = false;
        this.messages = []; // { role: "assistant"|"user", text: string }
        this.minTextLength = 10; // Minimum characters for free-text responses

        this.init();
    }

    appendMessage(role, text) {
        this.messages.push({ role, text });
        this.renderChat();
    }

    scrollComposerIntoView() {
        const composer = document.getElementById("composer");
        if (!composer) return;
        composer.scrollIntoView({ behavior: "smooth", block: "end" });
    }

    renderChat() {
        const chatLog = document.getElementById("chat-log");

        chatLog.innerHTML = this.messages.map(m => `
            <div class="line">
                <span class="role">${m.role === "assistant" ? "Interviewer:" : "You:"}</span>
                <span class="text">${this.escapeHtml(m.text)}</span>
            </div>
        `).join("");

        chatLog.scrollTop = chatLog.scrollHeight;
    }

    renderComposer() {
        const composer = document.getElementById("composer");
        const inputHost = document.getElementById("composer-input");

        composer.classList.remove("hidden");

        const q = this.currentQuestion;
        const isText = this.isFollowUp || q.question_type === "free_text";

        if (isText) {
            inputHost.innerHTML = `
                <label for="text-answer">Your answer:</label>
                <textarea id="text-answer" placeholder="Type your response..." rows="3"></textarea>
                <div id="input-feedback" class="input-feedback"></div>
            `;

            // Add real-time character count for text inputs
            const textarea = document.getElementById("text-answer");
            if (textarea) {
                textarea.addEventListener("input", () => {
                    this.updateTextFeedback(textarea.value.trim().length);
                });
            }
        } else if (q.question_type === "single_choice") {
            inputHost.innerHTML = `
                <div class="radio-group">
                    ${q.options.map(opt => `
                        <label class="radio-option">
                            <input type="radio" name="answer" value="${opt.option_id}" data-text="${this.escapeHtml(opt.text)}">
                            <span>${this.escapeHtml(opt.text)}</span>
                        </label>
                    `).join("")}
                </div>
                <div id="input-feedback" class="input-feedback"></div>
            `;
        }

        this.scrollComposerIntoView();

        // Prefer-not button only for non-followups
        const preferBtn = document.getElementById("prefer-not-btn");
        if (preferBtn) preferBtn.style.display = this.isFollowUp ? "none" : "inline-flex";
    }

    updateTextFeedback(length) {
        const feedback = document.getElementById("input-feedback");
        if (!feedback) return;

        if (length === 0) {
            feedback.textContent = "";
            feedback.className = "input-feedback";
        } else if (length < this.minTextLength) {
            feedback.textContent = `${this.minTextLength - length} more characters needed`;
            feedback.className = "input-feedback warning";
        } else {
            feedback.textContent = "✓ Ready to submit";
            feedback.className = "input-feedback success";
        }
    }

    async init() {
        // NEW: respondent ID (replaces old anonymousId)
        this.respondentId = getOrCreateRespondentId();
        displayRespondentId(this.respondentId);

        // Check for session recovery
        await this.checkSessionRecovery();

        // Setup event listeners
        this.setupEventListeners();
    }

    async checkSessionRecovery() {
        const savedSessionId = sessionStorage.getItem("survey_session_id");
        const savedPosition = sessionStorage.getItem("survey_position");

        if (savedSessionId && savedPosition) {
            const shouldRecover = confirm(
                "It looks like you have an incomplete survey. Would you like to continue where you left off?"
            );

            if (shouldRecover) {
                try {
                    this.sessionId = parseInt(savedSessionId);
                    this.currentPosition = parseInt(savedPosition);
                    
                    // Try to recover session (you may need to add a backend endpoint for this)
                    // For now, we'll just start fresh but this is the hook for recovery
                    console.log("Session recovery attempted:", this.sessionId);
                } catch (error) {
                    console.log("Could not recover session, starting fresh");
                }
            }

            // Clear old session data if not recovering or if recovery failed
            if (!shouldRecover) {
                sessionStorage.removeItem("survey_session_id");
                sessionStorage.removeItem("survey_position");
            }
        }

        // Start new or continue session
        await this.startSession();
    }

    async startSession() {
        try {
            this.showLoading("Starting survey...");

            const response = await api.startSession(
                CONFIG.SURVEY_ID,
                this.respondentId
            );

            this.sessionId = response.session_id;
            this.totalQuestions = response.total_questions;
            this.currentQuestion = response.first_question;
            this.currentPosition = response.first_question.position;
            this.isFollowUp = false;

            // Save session for recovery
            sessionStorage.setItem("survey_session_id", this.sessionId);
            sessionStorage.setItem("survey_position", this.currentPosition);

            this.hideLoading();

            this.messages = [];
            this.appendMessage("assistant", this.currentQuestion.question_text);

            this.renderComposer();
            this.updateProgress();

        } catch (error) {
            console.error("Full error:", error);
            this.showError(
                "We're having trouble connecting right now. Please check your internet connection and try again.",
                true // Show retry button
            );
        }
    }

    setupEventListeners() {
        if (this._listenersBound) return;
        this._listenersBound = true;

        // Submit button
        document.getElementById("send-btn")?.addEventListener("click", () => {
            this.submitAnswer();
        });

        // Prefer not to answer
        document.getElementById("prefer-not-btn")?.addEventListener("click", () => {
            this.submitPreferNotToAnswer();
        });

        // End interview
        document.getElementById("end-interview-btn")?.addEventListener("click", () => {
            this.confirmEndInterview();
        });

        // Radio button selection
        document.addEventListener("change", (e) => {
            if (e.target.type === "radio") {
                document.querySelectorAll(".radio-option").forEach(opt => {
                    opt.classList.remove("selected");
                });
                e.target.closest(".radio-option")?.classList.add("selected");
                
                // Clear any error messages when user makes selection
                this.clearError();
            }
        });

        // Enter key to submit (for textarea)
        document.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && e.ctrlKey) {
                const textarea = document.getElementById("text-answer");
                if (textarea === document.activeElement) {
                    this.submitAnswer();
                }
            }
        });
    }

    confirmEndInterview() {
        this.showConfirmDialog(
            "Are you sure you want to end the survey now?",
            "Your responses so far will be saved.",
            () => this.endInterview()
        );
    }

    showConfirmDialog(title, message, onConfirm) {
        const existing = document.getElementById("confirm-dialog");
        if (existing) existing.remove();

        const dialog = document.createElement("div");
        dialog.id = "confirm-dialog";
        dialog.className = "modal-overlay";
        dialog.innerHTML = `
            <div class="modal-content">
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="modal-actions">
                    <button id="confirm-yes" class="btn-primary">Yes, end survey</button>
                    <button id="confirm-no" class="btn-outline">Continue survey</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        document.getElementById("confirm-yes").addEventListener("click", () => {
            dialog.remove();
            onConfirm();
        });

        document.getElementById("confirm-no").addEventListener("click", () => {
            dialog.remove();
        });

        // Close on background click
        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });
    }

    async submitAnswer() {
        if (this.isLoading) return;

        try {
            const answer = this.getAnswer();
            if (!answer) {
                this.showInlineError("Please provide an answer before submitting.");
                return;
            }

            // Validate text length for free-text responses
            if (answer.answer_type === "free_text" || answer.answer_type === "follow_up_answer") {
                if (answer.text.length < this.minTextLength) {
                    this.showInlineError(
                        `Could you elaborate a bit more? We'd like at least ${this.minTextLength} characters to better understand your perspective.`
                    );
                    return;
                }
            }

            this.clearError();
            this.appendMessage("user", answer.text || "");

            const textarea = document.getElementById("text-answer");
            if (textarea) textarea.value = "";

            document.querySelectorAll('input[name="answer"]').forEach(r => (r.checked = false));
            document.querySelectorAll(".radio-option").forEach(opt => opt.classList.remove("selected"));

            this.showLoading("Reviewing your response...");
            const response = await api.submitAnswer(this.sessionId, answer);
            this.hideLoading();
            
            // Update session position
            sessionStorage.setItem("survey_position", this.currentPosition);
            
            this.handleResponse(response);

        } catch (error) {
            console.error("Submit error:", error);
            this.showError(
                "There was a problem submitting your response. Let me try that again.",
                true
            );
        }
    }

    async submitPreferNotToAnswer() {
        if (this.isLoading) return;

        try {
            this.showLoading("Processing...");

            const answer = {
                question_id: this.currentQuestion.question_id,
                answer_type: "prefer_not_to_answer",
                text: "Prefer not to answer"
            };

            this.appendMessage("user", "Prefer not to answer");
            const response = await api.submitAnswer(this.sessionId, answer);

            this.hideLoading();
            this.handleResponse(response);

        } catch (error) {
            console.error("Submit error:", error);
            this.showError(
                "There was a problem submitting your response. Please try again.",
                true
            );
        }
    }

    async endInterview() {
        try {
            this.showLoading("Finishing up...");

            const response = await api.endSession(this.sessionId);

            // Clear session recovery data
            sessionStorage.removeItem("survey_session_id");
            sessionStorage.removeItem("survey_position");

            this.hideLoading();
            this.showCompletion(response);

        } catch (error) {
            console.error("End session error:", error);
            this.showError(
                "There was a problem ending the survey. Your responses have been saved.",
                false
            );
        }
    }

    getAnswer() {
        if (this.isFollowUp || this.currentQuestion.question_type === "free_text") {
            const textarea = document.getElementById("text-answer");
            const text = textarea?.value.trim();

            if (!text) return null;

            return {
                question_id: this.isFollowUp ? null : this.currentQuestion.question_id,
                answer_type: this.isFollowUp ? "follow_up_answer" : "free_text",
                text
            };
        }

        if (this.currentQuestion.question_type === "single_choice") {
            const selected = document.querySelector('input[name="answer"]:checked');
            if (!selected) return null;

            return {
                question_id: this.currentQuestion.question_id,
                answer_type: "single_choice",
                selected_option_id: selected.value,
                text: selected.dataset.text
            };
        }

        return null;
    }

    handleResponse(response) {
        if (response.message_type === "completed") {
            this.showCompletion(response);
            return;
        }

        if (response.message_type === "follow_up_question") {
            this.isFollowUp = true;
            this.currentQuestion = { question_type: "free_text", question_text: response.question_text };
            this.appendMessage("assistant", response.question_text);
            this.renderComposer();
            return;
        }

        if (response.message_type === "survey_question") {
            this.isFollowUp = false;
            this.currentQuestion = response.question;
            this.currentPosition = response.question.position;
            this.appendMessage("assistant", response.question.question_text);
            this.updateProgress();
            this.renderComposer();
            return;
        }
    }

    showCompletion(response) {
        const summary = response.summary || {};
        const duration = summary.duration_seconds || 0;
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        
        let timeText = "";
        if (minutes > 0) {
            timeText = `${minutes} minute${minutes !== 1 ? 's' : ''}`;
            if (seconds > 0) timeText += ` and ${seconds} second${seconds !== 1 ? 's' : ''}`;
        } else {
            timeText = `${seconds} second${seconds !== 1 ? 's' : ''}`;
        }

        this.appendMessage("assistant",
            `Thank you for completing the survey! Your responses have been recorded.\n\n` +
            `Questions answered: ${summary.questions_answered || 0}\n` +
            `Time taken: ${timeText}`
        );

        document.getElementById("composer")?.classList.add("hidden");
        document.getElementById("progress-section")?.classList.add("hidden");

        // Clear session recovery data
        sessionStorage.removeItem("survey_session_id");
        sessionStorage.removeItem("survey_position");
    }

    updateProgress() {
        const progressSection = document.getElementById("progress-section");
        const progressBar = document.getElementById("progress-bar");
        const progressText = document.getElementById("progress-text");

        progressSection?.classList.remove("hidden");

        const progress = (this.currentPosition / this.totalQuestions) * 100;
        if (progressBar) progressBar.style.width = progress + "%";
        if (progressText) progressText.textContent = `Question ${this.currentPosition} of ${this.totalQuestions}`;
    }

    showLoading(message = "Processing...") {
        this.isLoading = true;
        const btn = document.getElementById("send-btn");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner"></span> ${message}`;
        }

        // Disable all inputs while loading
        document.querySelectorAll("input, textarea, button").forEach(el => {
            if (el.id !== "end-interview-btn") {
                el.disabled = true;
            }
        });
    }

    hideLoading() {
        this.isLoading = false;
        const btn = document.getElementById("send-btn");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = "Submit";
        }

        // Re-enable inputs
        document.querySelectorAll("input, textarea, button").forEach(el => {
            el.disabled = false;
        });
    }

    showInlineError(message) {
        const feedback = document.getElementById("input-feedback");
        if (feedback) {
            feedback.textContent = message;
            feedback.className = "input-feedback error";
        }
    }

    clearError() {
        const feedback = document.getElementById("input-feedback");
        if (feedback) {
            feedback.textContent = "";
            feedback.className = "input-feedback";
        }

        // Remove any error dialogs
        const errorDialog = document.getElementById("error-dialog");
        if (errorDialog) errorDialog.remove();
    }

    showError(message, showRetry = false) {
        this.hideLoading();
        
        // Remove existing error dialog
        const existing = document.getElementById("error-dialog");
        if (existing) existing.remove();

        const dialog = document.createElement("div");
        dialog.id = "error-dialog";
        dialog.className = "modal-overlay";
        
        const retryButton = showRetry ? 
            `<button id="error-retry" class="btn-primary">Try Again</button>` : '';

        dialog.innerHTML = `
            <div class="modal-content error-modal">
                <div class="error-icon">⚠️</div>
                <h3>Connection Issue</h3>
                <p>${message}</p>
                <div class="modal-actions">
                    ${retryButton}
                    <button id="error-close" class="btn-outline">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        if (showRetry) {
            document.getElementById("error-retry")?.addEventListener("click", () => {
                dialog.remove();
                // Retry the last action - for now just re-enable the form
                this.hideLoading();
            });
        }

        document.getElementById("error-close")?.addEventListener("click", () => {
            dialog.remove();
        });

        // Close on background click
        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    async typeText(el, text, {
        speedMs = 18,
        startDelayMs = 150,
        cursor = true
    } = {}) {
        if (!el) return;

        el.textContent = "";
        await new Promise(r => setTimeout(r, startDelayMs));

        let cursorEl = null;
        if (cursor) {
            cursorEl = document.createElement("span");
            cursorEl.textContent = "▍";
            cursorEl.style.marginLeft = "2px";
            cursorEl.style.display = "inline-block";
            el.appendChild(cursorEl);
        }

        for (let i = 0; i < text.length; i++) {
            if (cursorEl) {
                cursorEl.insertAdjacentText("beforebegin", text[i]);
            } else {
                el.insertAdjacentText("beforeend", text[i]);
            }
            await new Promise(r => setTimeout(r, speedMs));
        }

        if (cursorEl) cursorEl.remove();
    }
}

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    new SurveyApp();
});