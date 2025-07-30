% A3CheatSheet Class File
% A modern, creative LaTeX template for A3 portrait cheat sheets
% Created for educational purposes

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{a3cheatsheet}[2025/05/11 A3 Cheat Sheet Template]

% Option for dark mode
\newif\ifdarkmode\darkmodefalse
\DeclareOption{darkmode}{\darkmodetrue}
\ProcessOptions\relax

% Base class - explicitly set a3paper option
\LoadClass[a3paper,portrait,9pt]{article}  % Reduced base font size from 10pt to 9pt

% Required packages
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{geometry}
\RequirePackage{xcolor}
\RequirePackage{tikz}
\RequirePackage[most]{tcolorbox}
\RequirePackage{enumitem}
\RequirePackage{amsmath,amssymb,amsfonts}
\RequirePackage{mathtools}
\RequirePackage{bm}
\RequirePackage{physics}
\RequirePackage{graphicx}
\RequirePackage{hyperref}
\RequirePackage{multicol}
\RequirePackage{fontawesome5}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{helvet} % Ensure Helvetica is available
\RequirePackage{microtype}
\RequirePackage{anyfontsize}  % Added to support arbitrary font sizes
\RequirePackage{array}

% Define color schemes - Updated to use Viridis palette
% Viridis palette colors (from dark purple to bright yellow)
% Dark purple: #440154, Blue: #31688e, Teal: #35b779, Green: #6ece58, Yellow: #fde725

% Light mode colors - using Viridis palette (swapped blue and teal)
\definecolor{light-primarycolor}{RGB}{53, 183, 121} % Viridis teal (#35b779) - now primary
\definecolor{light-secondarycolor}{RGB}{49, 104, 142} % Viridis blue (#31688e) - now secondary
\definecolor{light-accentcolor}{RGB}{68, 1, 84} % Viridis dark purple (#440154)
\definecolor{light-backgroundcolor}{RGB}{250, 250, 250} % Very light gray
\definecolor{light-textcolor}{RGB}{68, 1, 84} % Viridis dark purple for text

% Dark mode colors - adjusted for better harmony with Helvetica
\definecolor{dark-primarycolor}{RGB}{102, 194, 165} % Softer teal-green for better harmony
\definecolor{dark-secondarycolor}{RGB}{252, 141, 98} % Warm coral instead of bright yellow
\definecolor{dark-accentcolor}{RGB}{141, 160, 203} % Soft blue-purple for accents
\definecolor{dark-backgroundcolor}{RGB}{28, 28, 35} % Slightly warmer dark background
\definecolor{dark-textcolor}{RGB}{255, 255, 255} % White for body text readability

% Apply color scheme based on mode
\ifdarkmode
  % Dark mode colors
  \colorlet{primarycolor}{dark-primarycolor}
  \colorlet{secondarycolor}{dark-secondarycolor}
  \colorlet{accentcolor}{dark-accentcolor}
  \colorlet{backgroundcolor}{dark-backgroundcolor}
  \colorlet{textcolor}{dark-textcolor}
\else
  % Light mode colors (default)
  \colorlet{primarycolor}{light-primarycolor}
  \colorlet{secondarycolor}{light-secondarycolor}
  \colorlet{accentcolor}{light-accentcolor}
  \colorlet{backgroundcolor}{light-backgroundcolor}
  \colorlet{textcolor}{light-textcolor}
\fi

% Page geometry - explicitly set a3paper option and dimensions
\geometry{
  a3paper,
  portrait,
  paperwidth=297mm,
  paperheight=420mm,
  margin=0.7cm,
  top=1cm,
  bottom=1cm,
  left=0.7cm,
  right=0.7cm,
  headheight=0.7cm,
  footskip=0.5cm
}

% Force PDF page size to match A3
\AtBeginDocument{
  \pdfpagewidth=\paperwidth
  \pdfpageheight=\paperheight
  % Ensure text color is properly set at the beginning of the document
  \color{textcolor}
}

% Set page color and font
\pagecolor{backgroundcolor}
\color{textcolor}
% Set Helvetica as the main font family
\renewcommand{\familydefault}{\sfdefault} % Use sans-serif (Helvetica) as default
\fontfamily{phv}\selectfont  % Explicitly set Helvetica
% Set main font size smaller
\fontsize{8pt}{9.6pt}\selectfont  % Added explicit font size reduction

% Header and footer
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[C]{\thepage}

% Reduce paragraph spacing
\setlength{\parskip}{0.5ex}
\setlength{\parindent}{0pt}

% Title format - reduced size and spacing with proper number-title separation
\titleformat{\section}
  {\color{primarycolor}\normalsize\bfseries}  % Reduced from large to normalsize
  {\thesection}
  {0.5em}  % Added space between number and title
  {}
  [\titlerule]

\titleformat{\subsection}
  {\color{secondarycolor}\small\bfseries}  % Reduced from normalsize to small
  {\thesubsection}
  {0.5em}  % Added space between number and title
  {}

\titleformat{\subsubsection}
  {\color{accentcolor}\footnotesize\bfseries}  % Reduced from small to footnotesize
  {\thesubsubsection}
  {0.5em}  % Added space between number and title
  {}

% Reduce section spacing
\titlespacing*{\section}{0pt}{1ex plus 1ex minus .2ex}{0.5ex plus .2ex}
\titlespacing*{\subsection}{0pt}{0.8ex plus 1ex minus .2ex}{0.3ex plus .2ex}
\titlespacing*{\subsubsection}{0pt}{0.6ex plus 1ex minus .2ex}{0.2ex plus .2ex}

% Custom title command - more compact with optional logo support
\newcommand{\cheatsheettitle}[3][]{%
  \begin{tcolorbox}[
    enhanced,
    colback=primarycolor,
    colframe=primarycolor,
    arc=0pt,
    outer arc=0pt,
    leftrule=0.7cm,
    rightrule=0pt,
    toprule=0pt,
    bottomrule=0pt,
    left=0.7cm,
    right=0.7cm,
    top=0.5cm,
    bottom=0.5cm,
    overlay={
      \node[anchor=west, text=white, font=\large\bfseries]  % Reduced from Large to large
        at ([xshift=0.3cm, yshift=0.2cm]frame.west) {#2};
      % Add subtitle below the main title
      \node[anchor=west, text=white, font=\small]
        at ([xshift=0.3cm, yshift=-0.2cm]frame.west) {#3};
      % Add logo if provided
      \ifx\relax#1\relax\else
        \node[anchor=east] at ([xshift=-0.3cm]frame.east) {
          \includegraphics[height=1cm]{#1}
        };
      \fi
    }
  ]
  % Remove the flushright content since subtitle is now in overlay
  \end{tcolorbox}
  \vspace{0.3cm}
}

% Command for adding images within sections
\newcommand{\sectionimage}[3][0.3]{%
  \begin{center}
    \includegraphics[width=#1\columnwidth]{#2}
    \ifx\relax#3\relax\else
      \\[2pt]
      \footnotesize\textit{#3}
    \fi
  \end{center}
  \vspace{2mm}
}

% Define box colors based on mode - Updated for Viridis palette
\ifdarkmode
  % Dark mode box colors - harmonized with new color scheme
  \definecolor{infobox-back}{RGB}{45, 85, 75} % Darker teal-green background
  \definecolor{formulabox-back}{RGB}{85, 60, 45} % Darker coral background
  \definecolor{notebox-back}{RGB}{60, 70, 85} % Darker blue-purple background
  \definecolor{box-text}{RGB}{255, 255, 255} % White text for readability
\else
  % Light mode box colors - using very light versions of Viridis colors (updated for swapped colors)
  \definecolor{infobox-back}{RGB}{240, 250, 245} % Very light teal tint (now primary)
  \definecolor{formulabox-back}{RGB}{240, 245, 250} % Very light blue tint (now secondary)
  \definecolor{notebox-back}{RGB}{248, 240, 250} % Very light purple tint
  \definecolor{box-text}{RGB}{68, 1, 84} % Viridis dark purple text
\fi

% Custom box environments - more compact with less padding
\newtcolorbox{infobox}[1][]{
  enhanced,
  colback=infobox-back,
  colframe=primarycolor,
  arc=2mm,
  title={#1},
  fonttitle=\bfseries\footnotesize,  % Reduced from small to footnotesize
  coltitle=white,
  colbacktitle=primarycolor,
  coltext=box-text,
  attach boxed title to top left={xshift=3mm, yshift=-2mm},
  boxed title style={arc=1.5mm},
  boxrule=0.8pt,
  left=2mm,
  right=2mm,
  top=5mm,
  bottom=2mm,
  before skip=2mm,
  after skip=2mm
}

\newtcolorbox{formulabox}[1][]{
  enhanced,
  colback=formulabox-back,
  colframe=secondarycolor,
  arc=2mm,
  title={#1},
  fonttitle=\bfseries\footnotesize,  % Reduced from small to footnotesize
  coltitle=white,
  colbacktitle=secondarycolor,
  coltext=box-text,
  attach boxed title to top left={xshift=3mm, yshift=-2mm},
  boxed title style={arc=1.5mm},
  boxrule=0.8pt,
  left=2mm,
  right=2mm,
  top=5mm,
  bottom=2mm,
  before skip=2mm,
  after skip=2mm
}

\newtcolorbox{notebox}[1][]{
  enhanced,
  colback=notebox-back,
  colframe=accentcolor,
  arc=2mm,
  title={#1},
  fonttitle=\bfseries\footnotesize,  % Reduced from small to footnotesize
  coltitle=white,
  colbacktitle=accentcolor,
  coltext=box-text,
  attach boxed title to top left={xshift=3mm, yshift=-2mm},
  boxed title style={arc=1.5mm},
  boxrule=0.8pt,
  left=2mm,
  right=2mm,
  top=5mm,
  bottom=2mm,
  before skip=2mm,
  after skip=2mm
}

% Custom list environments - more compact
\setlist{noitemsep, topsep=0pt, parsep=0pt, partopsep=0pt, leftmargin=*, font=\footnotesize}  % Added font=\footnotesize
\setlist[itemize]{noitemsep, topsep=0pt, parsep=0pt, partopsep=0pt, leftmargin=*, font=\footnotesize}
\setlist[enumerate]{noitemsep, topsep=0pt, parsep=0pt, partopsep=0pt, leftmargin=*, font=\footnotesize}

% Custom commands for common elements - more compact icons
\newcommand{\keypoint}[1]{\textcolor{primarycolor}{\footnotesize\faIcon{star}} {\footnotesize\textbf{#1}}}  % Reduced from small to footnotesize
\newcommand{\warning}[1]{\textcolor{red}{\footnotesize\faIcon{exclamation-triangle}} {\footnotesize\textbf{#1}}}  % Reduced from small to footnotesize
\newcommand{\tip}[1]{\textcolor{secondarycolor}{\footnotesize\faIcon{lightbulb}} {\footnotesize\textit{#1}}}  % Reduced from small to footnotesize

% Hyperref setup
\hypersetup{
  colorlinks=true,
  linkcolor=primarycolor,
  urlcolor=primarycolor,
  citecolor=accentcolor
}

% Multicol setup - reduced column separation
\setlength{\columnsep}{0.5cm}  % Reduced from 0.6cm to 0.5cm
\setlength{\columnseprule}{0.5pt}
\def\columnseprulecolor{\color{primarycolor!30}}

% Math settings for more compact equations
\setlength{\abovedisplayskip}{2pt}  % Reduced from 3pt to 2pt
\setlength{\belowdisplayskip}{2pt}  % Reduced from 3pt to 2pt
\setlength{\abovedisplayshortskip}{1pt}
\setlength{\belowdisplayshortskip}{1pt}
\setlength{\jot}{1.5pt}  % Reduced from 2pt to 1.5pt

% Math font size settings - improved for readability
% Keep inline math at normal size, only reduce display math
\everydisplay{\small}  % Use small font for display math only

% Dark mode math color adjustment
\ifdarkmode
  % Make math expressions use white in dark mode
  \everydisplay{\color{white}\small}
  \everymath{\color{white}}  % Inline math uses white but normal size
  
  % Ensure all text uses white in dark mode
  \AtBeginDocument{
    \color{white}
  }
\else
  % Light mode - inline math uses normal size, display math uses small
  \everymath{}  % No size change for inline math in light mode
\fi 