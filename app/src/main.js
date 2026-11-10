const journey = document.querySelector('#journey');
const toggle = document.querySelector('#toggle');
const speedButton = document.querySelector('#speed');
const pauseIcon = document.querySelector('#pause-icon');
const playIcon = document.querySelector('#play-icon');
const announcer = document.querySelector('#announcer');
const train = document.querySelector('#train');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let paused = reduceMotion.matches;
const speeds = [1, 1.5, 0.75];
let speedIndex = 0;

function renderPauseState(announce = false) {
  journey.classList.toggle('paused', paused);
  toggle.setAttribute('aria-pressed', String(paused));
  toggle.setAttribute('aria-label', paused ? '播放动画' : '暂停动画');
  pauseIcon.style.display = paused ? 'none' : 'block';
  playIcon.style.display = paused ? 'block' : 'none';
  if (announce) announcer.textContent = paused ? '动画已暂停' : '动画继续播放';
}

function toggleAnimation() {
  paused = !paused;
  renderPauseState(true);
}

toggle.addEventListener('click', toggleAnimation);
speedButton.addEventListener('click', () => {
  speedIndex = (speedIndex + 1) % speeds.length;
  const speed = speeds[speedIndex];
  train.style.animationDuration = `${28 / speed}s`;
  speedButton.dataset.speed = String(speed);
  document.querySelector('#speed-needle').setAttribute('transform', `rotate(${speedIndex * 42 - 84} 12 17)`);
  speedButton.setAttribute('aria-label', `当前${speed}倍速，点击切换速度`);
  announcer.textContent = `列车速度已切换为${speed}倍速`;
});

document.addEventListener('keydown', (event) => {
  if (event.code === 'Space' && !event.repeat && !event.target.closest('button')) {
    event.preventDefault();
    toggleAnimation();
  }
});

reduceMotion.addEventListener('change', (event) => {
  paused = event.matches;
  renderPauseState();
});

renderPauseState();
