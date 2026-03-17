/* ── Theme toggle with localStorage persistence ──────────────── */
(function () {
  var saved = localStorage.getItem('theme');
  if (saved === 'dark') document.documentElement.classList.add('dark');

  window.toggleTheme = function () {
    var dark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', dark ? 'dark' : 'light');
    var btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = dark ? '\u2600 Light' : '\uD83C\uDF19 Dark';
  };

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = document.documentElement.classList.contains('dark') ? '\u2600 Light' : '\uD83C\uDF19 Dark';
  });
})();
