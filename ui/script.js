const analyzeButton = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const resultsSection = document.getElementById('results');
const progressFill = document.querySelector('.progress-fill');
const resultCards = Array.from(document.querySelectorAll('[data-card]'));

function createRipple(event) {
  const ripple = document.createElement('span');
  ripple.className = 'ripple';

  const rect = analyzeButton.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);

  ripple.style.width = `${size}px`;
  ripple.style.height = `${size}px`;
  ripple.style.left = `${event.clientX - rect.left}px`;
  ripple.style.top = `${event.clientY - rect.top}px`;

  analyzeButton.appendChild(ripple);
  ripple.addEventListener('animationend', () => ripple.remove());
}

function showResults() {
  loadingState.hidden = true;
  resultsSection.hidden = false;

  resultCards.forEach((card, index) => {
    window.setTimeout(() => {
      card.classList.add('ready');
    }, 140 * index + 160);
  });
}

function runAnalysis() {
  analyzeButton.disabled = true;
  loadingState.hidden = false;
  resultsSection.hidden = true;
  resultCards.forEach((card) => card.classList.remove('ready'));

  let progress = 0;
  progressFill.style.width = '0%';

  const interval = window.setInterval(() => {
    progress += 7 + Math.floor(Math.random() * 8);
    if (progress >= 100) {
      progress = 100;
      window.clearInterval(interval);
      progressFill.style.width = '100%';
      window.setTimeout(showResults, 360);
      window.setTimeout(() => {
        analyzeButton.disabled = false;
      }, 1200);
    }

    progressFill.style.width = `${progress}%`;
  }, 90);
}

analyzeButton.addEventListener('click', (event) => {
  createRipple(event);
  runAnalysis();
});

window.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
});
