/* ── Sidebar: active-link observer + toggle ───────────────── */
document.addEventListener('DOMContentLoaded', function () {
  /* Active sidebar link via IntersectionObserver */
  var navLinks = document.querySelectorAll('nav.sidebar a.nav-item[href^="#"]');
  var targets = [];

  navLinks.forEach(function (link) {
    var id = link.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (el) targets.push({ el: el, link: link });
  });

  if (targets.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          navLinks.forEach(function (l) { l.classList.remove('active'); });
          var match = targets.find(function (t) { return t.el === entry.target; });
          if (match) match.link.classList.add('active');
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });

    targets.forEach(function (t) { observer.observe(t.el); });
  }

  /* Unified sidebar toggle — works on desktop and mobile */
  window.toggleSidebar = function () {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    if (window.innerWidth <= 900) {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('active');
    } else {
      sidebar.classList.toggle('collapsed');
    }
  };

  /* Legacy aliases */
  window.openSidebar = function () {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    if (window.innerWidth <= 900) {
      sidebar.classList.add('open');
      if (overlay) overlay.classList.add('active');
    } else {
      sidebar.classList.remove('collapsed');
    }
  };

  window.closeSidebar = function () {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
  };

  /* Close mobile sidebar on nav-item click */
  document.querySelectorAll('nav.sidebar a.nav-item').forEach(function (link) {
    link.addEventListener('click', function () {
      if (window.innerWidth <= 900) closeSidebar();
    });
  });
});
