/* PhotoBudka — Frontend logic */

const COUNTDOWN_SECONDS = 3;

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('screen-' + id).classList.add('active');
}

function showError(msg) {
    document.getElementById('error-message').textContent = msg;
    showScreen('error');
}

function reset() {
    showScreen('welcome');
}

/* ── Capture Flow ──────────────────────────────── */

function startCapture() {
    showScreen('preview');
    // Small delay to let the camera stream load
    setTimeout(() => startCountdown(), 500);
}

function startCountdown() {
    const el = document.getElementById('countdown');
    let count = COUNTDOWN_SECONDS;

    el.classList.remove('hidden');
    el.textContent = count;

    const interval = setInterval(() => {
        count--;
        if (count > 0) {
            el.textContent = count;
            // Re-trigger animation
            el.style.animation = 'none';
            el.offsetHeight; // force reflow
            el.style.animation = '';
        } else {
            clearInterval(interval);
            el.classList.add('hidden');
            doCapture();
        }
    }, 1000);
}

function doCapture() {
    // Flash effect
    const flash = document.getElementById('flash');
    flash.classList.add('active');
    setTimeout(() => flash.classList.remove('active'), 200);

    // Call server to capture
    fetch('/capture', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('captured-photo').src = data.image;
                showScreen('result');
            } else {
                showError(data.error || 'Ошибка при съёмке');
            }
        })
        .catch(err => {
            showError('Ошибка соединения с камерой');
            console.error(err);
        });
}

/* ── Print Flow ────────────────────────────────── */

function printPhoto() {
    showScreen('printing');

    fetch('/print', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showScreen('done');
                // Auto-return to welcome after 10 seconds
                setTimeout(() => {
                    if (document.getElementById('screen-done').classList.contains('active')) {
                        reset();
                    }
                }, 10000);
            } else {
                showError(data.message || 'Ошибка печати');
            }
        })
        .catch(err => {
            showError('Ошибка соединения с принтером');
            console.error(err);
        });
}

function retake() {
    startCapture();
}

/* ── Idle timeout: return to welcome after 60s of inactivity ── */

let idleTimer = null;

function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        // Only auto-reset if not on welcome screen
        if (!document.getElementById('screen-welcome').classList.contains('active')) {
            reset();
        }
    }, 60000);
}

document.addEventListener('click', resetIdleTimer);
document.addEventListener('touchstart', resetIdleTimer);
resetIdleTimer();
