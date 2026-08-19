// KIPAS Theme Manager
(function () {
  const STORAGE_KEY = 'kipas-theme';

  function getTheme() {
    return localStorage.getItem(STORAGE_KEY) ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    const btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
      btn.querySelector('.icon-sun')  && btn.querySelector('.icon-sun').classList.toggle('hidden', theme !== 'light');
      btn.querySelector('.icon-moon') && btn.querySelector('.icon-moon').classList.toggle('hidden', theme !== 'dark');
    }
  }

  // Apply immediately to avoid flash
  applyTheme(getTheme());

  window.toggleTheme = function () {
    const current = getTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    // Persist to server if logged in
    fetch('/api/v1/users/me/theme/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ dark_mode: next === 'dark' }),
    }).catch(() => {});
  };

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme(getTheme());
  });
})();

function getCsrf() {
  return document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}
