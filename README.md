# Resources

A selection of scripts, templates and tools for solving problems.

## Categories

- **Developer-Tools/**
  - `repo-dashboard.py`: A terminal-based dashboard that scans directories to provide a summary of code statistics, including language distribution, line counts, and file totals with color-coded ANSI output.

- **Mathematics/**
  - **Statistics**: A collection of resources for hypothesis testing, including a decision tree for selecting statistical tests, practice problems, and an interactive HTML reference.
  - **TSP (Travelling Salesman Problem)**:
    - Scripts for node and edge generation and solving TSP instances using graph theory and optimization.
  - **Numerical Methods**:
    - `NumericalMethods.html`: A self-contained interactive reference covering all four topics below — with formulas (MathJax), pseudocode, convergence orders, and a dark/light theme toggle.
    - **Interpolation** (`interpolation.py`): Lagrange polynomial, Newton's divided differences, and cubic spline interpolation. Includes a striking visualisation of Runge's phenomenon — showing how high-degree polynomials on equally-spaced nodes oscillate wildly — plus an artistic dark-background comparison plot.
    - **Root Finding** (`root_finding.py`): Bisection, Newton-Raphson, and Secant methods with a convergence comparison (log error vs iteration). Features an artistic Newton fractal — a colour map of which root of $z^3 - 1$ each starting point in the complex plane converges to.
    - **ODE Solvers** (`ode_solvers.py`): Forward Euler, Heun's (RK2), and classic RK4, with a global error vs step-size log-log convergence plot confirming each method's theoretical order. Includes an artistic phase-space portrait of a damped pendulum.
    - **Numerical Integration** (`quadrature.py`): Composite Trapezoidal, Simpson's 1/3 Rule, and Gauss-Legendre quadrature. Features a log-log convergence comparison and an artistic panel visualisation on a dark background.

- **Physics/**
  - `JupiterOrbitSimulator-Example.py`: An N-body physics simulation of the Galilean moons (Io, Europa, Ganymede, and Callisto) orbiting Jupiter. Includes Keplerian orbital element verification and 3D artistic visualizations.

- **Templates/**
  - **LaTeX**:
    - **A3 Exam Review Poster (Cheat Sheet) Template**: A large-format template for creating dense, organized revision posters.
    - **Scientific Article (Popular Account) Template**: A clean, professional layout for scientific writing and reports.
    - **Technical Reference (Info Sheet) Template**: A landscape A4 template designed for technical interview reference sheets, featuring syntax highlighting and modular content boxes.
