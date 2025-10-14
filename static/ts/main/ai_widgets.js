"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PracticeTestWidgetAI = void 0;
// main/ai_widgets.ts
class PracticeTestWidgetAI {
    modal;
    openButton;
    form;
    constructor(modalId, buttonId, formId) {
        this.modal = document.getElementById(modalId);
        this.openButton = document.getElementById(buttonId);
        this.form = document.getElementById(formId);
        this.setupListeners();
    }
    setupListeners() {
        // Open modal
        this.openButton.addEventListener('click', () => {
            this.modal.classList.add('show');
        });
        // Close modal on click outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.modal.classList.remove('show');
            }
        });
        // Handle form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = (this.form.querySelector('#title')).value;
            const subject = (this.form.querySelector('#subject')).value;
            console.log('Submitting AI Test:', { title, subject });
            // You can send AJAX / fetch request to Django here
            fetch('/create_ai_test/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCSRF() },
                body: JSON.stringify({ title, subject }),
            }).then(() => {
                this.modal.classList.remove('show');
                this.form.reset();
            });
        });
    }
    getCSRF() {
        const cookieValue = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieValue?.[1] ?? '';
    }
}
exports.PracticeTestWidgetAI = PracticeTestWidgetAI;
//# sourceMappingURL=ai_widgets.js.map