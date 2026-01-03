/**
 * Survey Application Logic
 */
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
        preferBtn.style.display = this.isFollowUp ? "none" : "inline-flex";
    }


    async init() {
        // Generate anonymous ID
        this.anonymousId = this.generateAnonymousId();
        
        // Start session
        await this.startSession();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    generateAnonymousId() {
        const stored = localStorage.getItem('survey_anonymous_id');
        if (stored) return stored;
        
        const newId = 'anon_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('survey_anonymous_id', newId);
        return newId;
    }

    async startSession() {
        try {
            this.showLoading('Starting survey...');
            
            const response = await api.startSession(
                CONFIG.SURVEY_ID,
                this.anonymousId
            );
            
            this.sessionId = response.session_id;
            this.totalQuestions = response.total_questions;
            this.currentQuestion = response.first_question;
            this.currentPosition = response.first_question.position;
            
            this.hideLoading();
            this.currentQuestion = response.first_question;
            this.currentPosition = response.first_question.position;
            this.isFollowUp = false;

            this.messages = [];
            this.appendMessage("assistant", this.currentQuestion.question_text);

            this.renderComposer();
            this.updateProgress();

            
        } catch (error) {
            this.showError('Failed to start survey: ' + error.message);
        }
    }

    setupEventListeners() {
        if (this._listenersBound) return;
        this._listenersBound = true;
        // Submit button
        document.getElementById('send-btn')?.addEventListener('click', () => {
        this.submitAnswer();
        });


        // Prefer not to answer
        document.getElementById('prefer-not-btn').addEventListener('click', () => {
            this.submitPreferNotToAnswer();
        });

        // End interview
        document.getElementById('end-interview-btn').addEventListener('click', () => {
            if (confirm('Are you sure you want to end the interview?')) {
                this.endInterview();
            }
        });

        // Radio button selection
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio') {
                // Highlight selected option
                document.querySelectorAll('.radio-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                e.target.closest('.radio-option').classList.add('selected');
            }
        });
    }

    async renderQuestion() {
        const container = document.getElementById('question-container');
        const question = this.currentQuestion;

        // Update progress
        this.updateProgress();

        // Question number and type
        const questionNumber = this.isFollowUp
            ? `<div class="followup-badge">Follow-up Question</div>`
            : `<div class="question-number">Question ${this.currentPosition} of ${this.totalQuestions}</div>`;

        // Question text (plain text)
        const questionText = this.isFollowUp
            ? (this.currentQuestion.question_text || "")
            : (question.question_text || "");

        // Build answer input based on type
        let answerHtml = '';

        if (this.isFollowUp || question.question_type === 'free_text') {
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
        } else if (question.question_type === 'single_choice') {
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
                `).join('')}
                </div>
            </div>
            `;
        }

        // Render with a placeholder for typed question text
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
                ` : ''}
                <button id="end-interview-btn" class="btn-danger">
                End Interview
                </button>
            </div>
            </div>
        `;

        // Re-attach event listeners (your existing method)
        this.setupEventListeners();

        // --- 3B: disable inputs while typing (keep End Interview enabled) ---
        const setInputsEnabled = (enabled) => {
            // Disable answer inputs
            container.querySelectorAll('input, textarea, button').forEach(el => {
            if (el.id === 'end-interview-btn') return; // keep escape hatch
            el.disabled = !enabled;
            });
        };

        // --- 3A: adjust typing speed for long questions ---
        const speedMs = questionText.length > 160 ? 8 : 18;

        // Type the question
        const typedEl = document.getElementById('question-text-typed');
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

            // ✅ CLEAR INPUTS HERE (after capturing answer, before API call)
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
            this.showLoading('Submitting...');
            
            const answer = {
                question_id: this.currentQuestion.question_id,
                answer_type: 'prefer_not_to_answer',
                text: 'Prefer not to answer'
            };
            this.appendMessage("user", "Prefer not to answer");
            const response = await api.submitAnswer(this.sessionId, answer);
            
            this.hideLoading();
            this.handleResponse(response);
            
        } catch (error) {
            this.showError('Failed to submit: ' + error.message);
        }
    }

    async endInterview() {
        try {
            this.showLoading('Ending interview...');
            
            const response = await api.endSession(this.sessionId);
            
            this.hideLoading();
            this.showCompletion(response);
            
        } catch (error) {
            this.showError('Failed to end interview: ' + error.message);
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
            this.showCompletion(response); // could become a final assistant bubble + disable composer
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
        const progressSection = document.getElementById('progress-section');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        progressSection.classList.remove('hidden');
        
        const progress = (this.currentPosition / this.totalQuestions) * 100;
        progressBar.style.width = progress + '%';
        progressText.textContent = `Question ${this.currentPosition} of ${this.totalQuestions}`;
    }

    showLoading(message = 'Loading...') {
        this.isLoading = true;
        const btn = document.getElementById('send-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner"></span> ${message}`;
        }
    }

    hideLoading() {
        this.isLoading = false;
        const btn = document.getElementById('send-btn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Submit';
        }
    }

    showError(message) {
        this.hideLoading();
        alert('Error: ' + message);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async typeText(el, text, {
        speedMs = 18,
        startDelayMs = 150,
        cursor = true
        } = {}) {
        if (!el) return;

        // Clear and prepare
        el.textContent = "";
        await new Promise(r => setTimeout(r, startDelayMs));

        // Optional cursor
        let cursorEl = null;
        if (cursor) {
            cursorEl = document.createElement("span");
            cursorEl.textContent = "▍";
            cursorEl.style.marginLeft = "2px";
            cursorEl.style.display = "inline-block";
            el.appendChild(cursorEl);
        }

        // Type character by character
        for (let i = 0; i < text.length; i++) {
            // insert before cursor if cursor exists
            if (cursorEl) {
            cursorEl.insertAdjacentText("beforebegin", text[i]);
            } else {
            el.insertAdjacentText("beforeend", text[i]);
            }
            await new Promise(r => setTimeout(r, speedMs));
        }

        // Remove cursor at end
        if (cursorEl) cursorEl.remove();
    }

}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SurveyApp();
});