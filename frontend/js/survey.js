// ===============================
// Respondent ID helpers (NEW)
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
            `;
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
            `;
        }

        // ✅ make sure options are visible immediately
        this.scrollComposerIntoView();

        // Prefer-not button only for non-followups (your current rule)
        const preferBtn = document.getElementById("prefer-not-btn");
        if (preferBtn) preferBtn.style.display = this.isFollowUp ? "none" : "inline-flex";
    }

    async init() {
        // NEW: respondent ID (replaces old anonymousId)
        this.respondentId = getOrCreateRespondentId();
        displayRespondentId(this.respondentId);

        // Start session
        await this.startSession();

        // Setup event listeners
        this.setupEventListeners();
    }

    // NOTE: keep this around if other code references it, but it is no longer used.
    generateAnonymousId() {
        const stored = localStorage.getItem("survey_anonymous_id");
        if (stored) return stored;

        const newId = "anon_" + Math.random().toString(36).substr(2, 9);
        localStorage.setItem("survey_anonymous_id", newId);
        return newId;
    }

    async startSession() {
        try {
            this.showLoading("Starting survey...");

            // Pass respondentId into your existing API wrapper.
            // This assumes api.startSession(surveyId, respondentId) sends it to backend.
            const response = await api.startSession(
                CONFIG.SURVEY_ID,
                this.respondentId
            );

            this.sessionId = response.session_id;
            this.totalQuestions = response.total_questions;
            this.currentQuestion = response.first_question;
            this.currentPosition = response.first_question.position;
            this.isFollowUp = false;

            this.hideLoading();

            this.messages = [];
            this.appendMessage("assistant", this.currentQuestion.question_text);

            this.renderComposer();
            this.updateProgress();

        } catch (error) {
            console.error("Full error:", error); // 👈 Add this
            this.showError("Failed to start survey: " + error.message);
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
            if (confirm("Are you sure you want to end the interview?")) {
                this.endInterview();
            }
        });

        // Radio button selection
        document.addEventListener("change", (e) => {
            if (e.target.type === "radio") {
                document.querySelectorAll(".radio-option").forEach(opt => {
                    opt.classList.remove("selected");
                });
                e.target.closest(".radio-option")?.classList.add("selected");
            }
        });
    }

    async renderQuestion() {
        const container = document.getElementById("question-container");
        const question = this.currentQuestion;

        // Update progress
        this.updateProgress();

        const questionNumber = this.isFollowUp
            ? `<div class="followup-badge">Follow-up Question</div>`
            : `<div class="question-number">Question ${this.currentPosition} of ${this.totalQuestions}</div>`;

        const questionText = this.isFollowUp
            ? (this.currentQuestion.question_text || "")
            : (question.question_text || "");

        let answerHtml = "";

        if (this.isFollowUp || question.question_type === "free_text") {
            answerHtml = `
            <div class="answer-section">
                <label for="text-answer">Your answer:</label>
                <textarea
                id="text-answer"
                placeholder="Type your response here..."
                rows="4"
                ></textarea>
            </div>
            `;
        } else if (question.question_type === "single_choice") {
            answerHtml = `
            <div class="answer-section">
                <div class="radio-group">
                ${(question.options || []).map(opt => `
                    <label class="radio-option">
                    <input
                        type="radio"
                        name="answer"
                        value="${opt.option_id}"
                        data-text="${this.escapeHtml(opt.text)}"
                    >
                    <span>${this.escapeHtml(opt.text)}</span>
                    </label>
                `).join("")}
                </div>
            </div>
            `;
        }

        container.innerHTML = `
            <div class="card question-card">
            ${questionNumber}
            <div class="question-text">
                <span id="question-text-typed"></span>
            </div>
            ${answerHtml}
            <div class="action-buttons">
                <button id="submit-btn" class="btn-primary">
                Submit Answer
                </button>
                ${!this.isFollowUp ? `
                <button id="prefer-not-btn" class="btn-outline">
                    Prefer Not To Answer
                </button>
                ` : ""}
                <button id="end-interview-btn" class="btn-danger">
                End Interview
                </button>
            </div>
            </div>
        `;

        this.setupEventListeners();

        const setInputsEnabled = (enabled) => {
            container.querySelectorAll("input, textarea, button").forEach(el => {
                if (el.id === "end-interview-btn") return;
                el.disabled = !enabled;
            });
        };

        const speedMs = questionText.length > 160 ? 8 : 18;

        const typedEl = document.getElementById("question-text-typed");
        setInputsEnabled(false);
        await this.typeText(typedEl, questionText, { speedMs, startDelayMs: 120, cursor: true });
        setInputsEnabled(true);
    }

    async submitAnswer() {
        if (this.isLoading) return;

        try {
            const answer = this.getAnswer();
            if (!answer) {
                alert("Please provide an answer before sending.");
                return;
            }

            this.appendMessage("user", answer.text || "");

            const textarea = document.getElementById("text-answer");
            if (textarea) textarea.value = "";

            document.querySelectorAll('input[name="answer"]').forEach(r => (r.checked = false));
            document.querySelectorAll(".radio-option").forEach(opt => opt.classList.remove("selected"));

            this.showLoading("Sending...");
            const response = await api.submitAnswer(this.sessionId, answer);
            this.hideLoading();
            this.handleResponse(response);

        } catch (error) {
            this.showError("Failed to submit answer: " + error.message);
        }
    }

    async submitPreferNotToAnswer() {
        if (this.isLoading) return;

        try {
            this.showLoading("Submitting...");

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
            this.showError("Failed to submit: " + error.message);
        }
    }

    async endInterview() {
        try {
            this.showLoading("Ending interview...");

            const response = await api.endSession(this.sessionId);

            this.hideLoading();
            this.showCompletion(response);

        } catch (error) {
            this.showError("Failed to end interview: " + error.message);
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
        this.appendMessage("assistant",
            `Thanks! You're all set.\n\nQuestions answered: ${summary.questions_answered || 0}\nTime: ${Math.floor((summary.duration_seconds || 0) / 60)} min`
        );

        document.getElementById("composer")?.classList.add("hidden");
        document.getElementById("progress-section")?.classList.add("hidden");
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

    showLoading(message = "Loading...") {
        this.isLoading = true;
        const btn = document.getElementById("send-btn");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner"></span> ${message}`;
        }
    }

    hideLoading() {
        this.isLoading = false;
        const btn = document.getElementById("send-btn");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = "Submit";
        }
    }

    showError(message) {
        this.hideLoading();
        alert("Error: " + message);
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
