# Resources

A selection of scripts, templates and tools for solving problems.

---

The best way to explore these resources is through the online dashboard:

**[matthewd0yle.com/Resources](https://matthewd0yle.com/Resources/)** — live site

You can also browse the repo structure directly in GitHub, but the website provides superior organisation and readability.

## Categories

- **Analysis/**
  - **Step-Detection**: Detect abrupt step changes in noisy 1D data using a rolling average and threshold. MATLAB implementation with a core detection function (`detectStepChange.m`) and a demo script (`testStepChange.m`) that generates synthetic data and plots results.

- **Dev-Tools/**
  - `repo-dashboard.py`: A terminal-based dashboard that scans directories to provide a summary of code statistics, including language distribution, line counts, and file totals with color-coded ANSI output.
  - **Resource Workbench** (`workbench/`): A Textual-based TUI that auto-discovers and runs every script in the repo. Features a tree-browser, async subprocess execution, built-in help, settings screen, and theming. Configured via `runner.toml`.

- **Mathematics/**
  - **Hypothesis Testing**: A collection of resources for hypothesis testing, including a decision tree for selecting statistical tests, practice problems, and an interactive HTML reference.
  - **TSP (Travelling Salesman Problem)**:
    - Scripts for node and edge generation and solving TSP instances using graph theory and optimization.
  - **Numerical Methods** — Each topic has its own interactive HTML reference with MathJax formulas, code examples, and a dark/light theme toggle. Includes Python scripts that generate diagnostic and artistic visualisations.
    - **Interpolation** (`interpolation.py`): Lagrange polynomial, Newton's divided differences, and cubic spline interpolation. Includes a striking visualisation of Runge's phenomenon — showing how high-degree polynomials on equally-spaced nodes oscillate wildly — plus an artistic dark-background comparison plot.
    - **Root Finding** (`root_finding.py`): Bisection, Newton-Raphson, and Secant methods with a convergence comparison (log error vs iteration). Features an artistic Newton fractal — a colour map of which root of $z^3 - 1$ each starting point in the complex plane converges to.
    - **ODE Solvers** (`ode_solvers.py`): Forward Euler, Heun's (RK2), and classic RK4, with a global error vs step-size log-log convergence plot confirming each method's theoretical order. Includes an artistic phase-space portrait of a damped pendulum.
    - **Numerical Integration** (`quadrature.py`): Composite Trapezoidal, Simpson's 1/3 Rule, and Gauss-Legendre quadrature. Features a log-log convergence comparison and an artistic panel visualisation on a dark background.
    - **FFT-Spectral** (`fft_spectral.py`): Discrete Fourier Transform and spectral analysis. Demonstrates FFT-based frequency decomposition with diagnostic and artistic visualisations.
    - **Chaos & Dynamical Systems** (`chaos_dynamics.py`): Logistic map, bifurcation diagrams, Lyapunov exponents, the Lorenz attractor, and the double pendulum. Includes cobweb diagrams, a sensitivity-to-initial-conditions study, and three artistic visualisations — a 3D Lorenz attractor colour-coded by speed, a double pendulum sensitivity mosaic, and a high-density bifurcation fractal.
    - **Reaction-Diffusion** (`reaction_diffusion.py`): Gray-Scott model simulating Turing pattern formation — spots, stripes, coral labyrinths, and self-replicating structures emerging from two diffusing chemicals. Uses a 5-point Laplacian stencil with periodic boundaries and forward Euler integration. Features a diagnostic time-evolution panel, a high-resolution four-regime Turing mosaic, and an artistic gradient-magnitude visualisation of reaction fronts.

- **Image-Vectorizer/**
  - `vectorize.py`: Converts raster images (PNG, JPG, BMP, GIF, TIFF, WebP) to SVG vector graphics. Uses k-means++ colour quantization, contour tracing, Ramer-Douglas-Peucker path simplification, and optional cubic Bezier fitting. Configurable colour count, detail level, and input scaling.

- **Physics/**
  - **Jupiter-Satellite-Orbits** (`JupiterOrbitSimulator-Example.py`): An N-body physics simulation of the Galilean moons (Io, Europa, Ganymede, and Callisto) orbiting Jupiter. Includes Keplerian orbital element verification and 3D artistic visualizations.
  - **Percolation** (`percolation.py`, `percolation_variants.py`): Site percolation on the square lattice — spanning probability, order parameter, cluster-size distributions, and finite-size scaling collapse with exact 2D critical exponents. Includes five variant models: gradient, explosive (Achlioptas), bootstrap ($k$-core), invasion, and directed percolation, each with diagnostic plots, artistic visualisations, and animated GIFs.

- **Templates/**
  - **LaTeX**:
    - **A3 Exam Review Poster (Cheat Sheet) Template**: A large-format template for creating dense, organized revision posters.
    - **Scientific Article (Popular Account) Template**: A clean, professional layout for scientific writing and reports.
    - **Technical Reference (Info Sheet) Template**: A landscape A4 template designed for technical interview reference sheets, featuring syntax highlighting and modular content boxes.
    - **Physics Poster Template**: A competition-quality A0 portrait poster template using `tikzposter`, with a deep purple & emerald green colour scheme, SI unit support, and QR code generation.
