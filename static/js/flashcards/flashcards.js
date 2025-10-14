// -------------------------
// Flashcards client logic
// Fully external JS compatible with inline server data
// -------------------------

// --- Data passed from HTML inline script ---
const allFlashcards = flashcardData.allFlashcards;
let currentCard = flashcardData.initialCard;
let currentIndex = 0;
let csrfToken = flashcardData.csrfToken;
const totalCards = flashcardData.totalCards;
let studyMode = flashcardData.studyModeInitial;

// --- Runtime state ---
let isFlipped = false;
let isProcessing = false;
let stats = { known: 0, notKnown: 0 };

// --- Elements ---
const flashcard = document.getElementById('flashcard');
const flashcardInner = document.getElementById('flashcardInner');
const frontContent = document.getElementById('frontContent');
const backContent = document.getElementById('backContent');
const flipBtn = document.getElementById('flipBtn');
const knownBtn = document.getElementById('knownBtn');
const notKnownBtn = document.getElementById('notKnownBtn');
const backBtn = document.getElementById('backBtn');
const proceedBtn = document.getElementById('proceedBtn');
const shuffleBtn = document.getElementById('shuffleBtn');
const toggleModeInput = document.getElementById('toggleMode');
const studyButtons = document.getElementById('study_mode_buttons');
const regularButtons = document.getElementById('regular_mode_buttons');
const statsArea = document.getElementById('statsArea');
const knownCountEl = document.getElementById('knownCount');
const notKnownCountEl = document.getElementById('notKnownCount');
const currentIndexEl = document.getElementById('currentIndex');
const progressFill = document.getElementById('progressFill');
const helpBtn = document.getElementById('helpBtn');
const shortcutsModal = document.getElementById('shortcutsModal');
const closeModal = document.getElementById('closeModal');
const exitBtn = document.getElementById('exitBtn');
const exitModal = document.getElementById('exitModal');
const cancelExit = document.getElementById('cancelExit');
const confirmExit = document.getElementById('confirmExit');

// -------------------------
// Utility Functions
// -------------------------

function renderCard(card) {
    if (!frontContent || !backContent) return;
    frontContent.textContent = card.front || '';
    backContent.textContent = card.back || '';
}

function updateProgress(idx) {
    if (currentIndexEl) currentIndexEl.textContent = idx + 1;
    if (progressFill) progressFill.style.width = ((idx + 1) / totalCards) * 100 + '%';
}

function updateStatsUI() {
    knownCountEl.textContent = stats.known;
    notKnownCountEl.textContent = stats.notKnown;
}

function updateNavButtons() {
    backBtn.disabled = currentIndex === 0;
    proceedBtn.disabled = currentIndex >= allFlashcards.length - 1;
}

function applyModeUI() {
    if (studyMode) {
        studyButtons.classList.remove('hidden');
        regularButtons.classList.add('hidden');
        statsArea.style.display = 'flex';
    } else {
        studyButtons.classList.add('hidden');
        regularButtons.classList.remove('hidden');
        statsArea.style.display = 'none';
    }
}

function animateCardChange(card) {
    const timeout = 150;
    flashcard.style.transition = `transform ${timeout}ms ease, opacity ${timeout}ms ease`;
    flashcard.style.transform = 'translateY(-12px) scale(0.98)';
    flashcard.style.opacity = '0.3';
    setTimeout(() => {
        renderCard(card);
        flashcard.style.transform = 'translateY(0) scale(1)';
        flashcard.style.opacity = '1';
    }, timeout);
}

async function postJSON(url, payload) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Network response not ok');
    return res.json();
}

async function resetSessionOnServer() {
    try {
        await postJSON(flashcardData.resetUrl, { mode: studyMode ? 'study' : 'regular' });
    } catch (err) {
        console.warn('Failed to reset server session, continuing locally.');
    }
}

// -------------------------
// Card Navigation
// -------------------------

function flipCard() {
    if (isProcessing) return;
    isFlipped = !isFlipped;
    flashcardInner.classList.toggle('flipped');
}

function shuffle() {
    for (let i = allFlashcards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [allFlashcards[i], allFlashcards[j]] = [allFlashcards[j], allFlashcards[i]];
    }
    resetLocalState();
}

function studyAnswer(action) {
    if (action === 'known') stats.known++;
    else stats.notKnown++;

    currentIndex++;
    if (currentIndex >= allFlashcards.length) return finishSession();

    currentCard = allFlashcards[currentIndex];
    animateCardChange(currentCard);
    updateProgress(currentIndex);
    updateNavButtons();
    updateStatsUI();
}

function regularNavigate(direction) {
    if (direction === 'next' && currentIndex < allFlashcards.length - 1) currentIndex++;
    else if (direction === 'prev' && currentIndex > 0) currentIndex--;
    else return;

    currentCard = allFlashcards[currentIndex];
    animateCardChange(currentCard);
    updateProgress(currentIndex);
    updateNavButtons();
}

// -------------------------
// Session Control
// -------------------------

function resetLocalState() {
    stats = { known: 0, notKnown: 0 };
    updateStatsUI();
    currentIndex = 0;
    currentCard = allFlashcards[currentIndex];
    animateCardChange(currentCard);
    updateProgress(currentIndex);
    updateNavButtons();
}

toggleModeInput.addEventListener('change', async (ev) => {
    studyMode = ev.target.checked;
    applyModeUI();
    resetLocalState();
    await resetSessionOnServer();
});

// -------------------------
// Keyboard Shortcuts
// -------------------------

document.addEventListener('keydown', (e) => {
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || e.metaKey || e.ctrlKey) return;

    if (e.key === ' ') { e.preventDefault(); flipCard(); return; }

    if (studyMode) {
        if (e.key === '1') { e.preventDefault(); studyAnswer('not_known'); return; }
        if (e.key === '2') { e.preventDefault(); studyAnswer('known'); return; }
    } else {
        if (e.key === 'ArrowRight') { e.preventDefault(); regularNavigate('next'); return; }
        if (e.key === 'ArrowLeft') { e.preventDefault(); regularNavigate('prev'); return; }
    }

    if (e.key === '?') { e.preventDefault(); shortcutsModal.style.display = 'flex'; shortcutsModal.setAttribute('aria-hidden','false'); }
    if (e.key === 'Escape') { shortcutsModal.style.display = 'none'; exitModal.style.display = 'none'; shortcutsModal.setAttribute('aria-hidden','true'); }
});

// -------------------------
// Event Listeners
// -------------------------

// document.addEventListener('DOMContentLoaded', () => {
//     renderCard(currentCard);
//     updateProgress(currentIndex);
//     updateStatsUI();
//     updateNavButtons();
//     applyModeUI();
// });

window.addEventListener('load', () => {
    // Ensure the flashcard is rendered immediately
    renderCard(currentCard);
    applyModeUI();
    updateProgress(currentIndex);
    updateStatsUI();
    updateNavButtons();
});


flashcard.addEventListener('click', flipCard);
flipBtn.addEventListener('click', flipCard);
shuffleBtn.addEventListener('click', shuffle);
knownBtn.addEventListener('click', () => studyAnswer('known'));
notKnownBtn.addEventListener('click', () => studyAnswer('not_known'));
proceedBtn.addEventListener('click', () => regularNavigate('next'));
backBtn.addEventListener('click', () => regularNavigate('prev'));

// Modals
helpBtn.addEventListener('click', () => { shortcutsModal.style.display = 'flex'; shortcutsModal.setAttribute('aria-hidden','false'); });
closeModal.addEventListener('click', () => { shortcutsModal.style.display = 'none'; shortcutsModal.setAttribute('aria-hidden','true'); });
shortcutsModal.addEventListener('click', (e) => { if (e.target === shortcutsModal) shortcutsModal.style.display='none'; });
exitBtn.addEventListener('click', () => { exitModal.style.display='flex'; exitModal.setAttribute('aria-hidden','false'); });
cancelExit.addEventListener('click', () => { exitModal.style.display='none'; exitModal.setAttribute('aria-hidden','true'); });
confirmExit.addEventListener('click', () => { window.location.href = flashcardData.exitUrl; });
exitModal.addEventListener('click', (e) => { if (e.target === exitModal) exitModal.style.display='none'; });

// -------------------------
// Finish Session
// -------------------------

async function finishSession() {
    const payload = {
        known: stats.known,
        not_known: stats.notKnown,
        total: allFlashcards.length
    };
    try {
        const res = await fetch(flashcardData.answerUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        console.log("Session saved:", data);

        const summaryEl = document.getElementById('summary');
        if (summaryEl) summaryEl.textContent = `Done! Known: ${stats.known}, Not known: ${stats.notKnown}`;
    } catch (err) {
        console.error('Failed to save session:', err);
    }
}
