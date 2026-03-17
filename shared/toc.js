var SITE_TOC = [
  {
    label: 'Explore',
    items: [
      { label: 'Image Gallery', href: '/shared/gallery.html' }
    ]
  },
  {
    label: 'Mathematics',
    items: [
      { label: 'Interpolation',         href: '/shared/md.html?src=Mathematics/Numerical-Methods/Interpolation/README.md' },
      { label: 'Root Finding',          href: '/shared/md.html?src=Mathematics/Numerical-Methods/Root-Finding/README.md' },
      { label: 'ODE Solvers',           href: '/shared/md.html?src=Mathematics/Numerical-Methods/ODE-Solvers/README.md' },
      { label: 'Numerical Integration', href: '/shared/md.html?src=Mathematics/Numerical-Methods/Numerical-Integration/README.md' },
      { label: 'FFT & Spectral',        href: '/shared/md.html?src=Mathematics/Numerical-Methods/FFT-Spectral/README.md' },
      { label: 'Chaos & Dynamics',      href: '/shared/md.html?src=Mathematics/Numerical-Methods/Chaos-Dynamics/README.md' },
      { label: 'Reaction-Diffusion',    href: '/shared/md.html?src=Mathematics/Numerical-Methods/Reaction-Diffusion/README.md' },
      { label: 'Hypothesis Testing',    href: '/Mathematics/Hypothesis Testing/HypothesisTesting.html' },
      { label: 'HT Decision Tree',      href: '/shared/md.html?src=Mathematics/Hypothesis Testing/HypothesisTestingDecisionTree.pdf', pdf: true },
      { label: 'HT Practice',           href: '/shared/md.html?src=Mathematics/Hypothesis Testing/HypothesisTestingPractice.pdf', pdf: true },
      { label: 'Travelling Salesman',   href: '/shared/md.html?src=Mathematics/TSP/README.md' }
    ]
  },
  {
    label: 'Analysis',
    items: [
      { label: 'Step Detection', href: '/shared/md.html?src=Analysis/Step-Detection/README.md' }
    ]
  },
  {
    label: 'Physics',
    items: [
      { label: 'Jupiter Satellite Orbits', href: 'https://github.com/matthewjdoyle/Resources/tree/main/Physics/Jupiter-Satellite-Orbits', external: true }
    ]
  },
  {
    label: 'Dev-Tools',
    items: [
      { label: 'Overview',           href: '/shared/md.html?src=Dev-Tools/README.md' },
      { label: 'Repo Dashboard',     href: 'https://github.com/matthewjdoyle/Resources/tree/main/Dev-Tools', external: true },
      { label: 'README Coverage',    href: 'https://github.com/matthewjdoyle/Resources/tree/main/Dev-Tools/readme-coverage.py', external: true },
      { label: 'Resource Workbench', href: '/shared/md.html?src=Dev-Tools/workbench/README.md' }
    ]
  },
  {
    label: 'Templates',
    items: [
      { label: 'A3 Exam Poster',      href: '/shared/md.html?src=Templates/LaTeX/A3 Exam Poster Template/README.md' },
      { label: 'A3 Poster',           href: '/shared/md.html?src=Templates/LaTeX/A3 Exam Poster Template/template.pdf', pdf: true },
      { label: 'Scientific Article',  href: 'https://github.com/matthewjdoyle/Resources/tree/main/Templates/LaTeX/Popular%20Account%20Template', external: true },
      { label: 'Sci. Article',        href: '/shared/md.html?src=Templates/LaTeX/Popular Account Template/main.pdf', pdf: true },
      { label: 'Technical Reference', href: '/shared/md.html?src=Templates/LaTeX/Info Sheet/README.md' },
      { label: 'Info Sheet',          href: '/shared/md.html?src=Templates/LaTeX/Info Sheet/main.pdf', pdf: true },
      { label: 'Physics Poster',      href: '/shared/md.html?src=Templates/LaTeX/Physics Poster Template/README.md' },
      { label: 'Physics Poster',       href: '/shared/md.html?src=Templates/LaTeX/Physics Poster Template/physics_poster.pdf', pdf: true }
    ]
  }
];

/**
 * Render the site TOC into `containerId`.
 * `currentHref` — the full href of the active page (optional), used to
 *   apply the `.current` class. Pass null on the dashboard.
 */
function renderTOC(containerId, currentHref) {
  var html = '';
  for (var s = 0; s < SITE_TOC.length; s++) {
    var section = SITE_TOC[s];
    html += '<span class="nav-section">' + section.label + '</span>';
    for (var i = 0; i < section.items.length; i++) {
      var item = section.items[i];
      var isCurrent = currentHref && item.href === currentHref;
      var cls = 'nav-item toc-item' + (isCurrent ? ' current' : '');
      var attrs = item.external ? ' target="_blank" rel="noopener"' : '';
      var label = item.label
        + (item.pdf      ? ' <span class="pdf-badge">(PDF)</span>' : '')
        + (item.external ? ' <span class="ext-icon">↗</span>'    : '');
      html += '<a class="' + cls + '" href="' + item.href + '"' + attrs + '>' + label + '</a>';
    }
  }
  document.getElementById(containerId).innerHTML = html;
}
