%% problem.cls  --  class based on article with homework/problem styling
%% Save as: problem.cls
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{problem}[Integrated Core problem style class]

% Pass all unknown options to article (e.g. 10pt/11pt/12pt, oneside/twoside, etc.)
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

% Base class
\LoadClass{article}

% =========================
% Packages
% =========================
% Font/math
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage[fleqn]{amsmath}
\RequirePackage{mathtools}
\RequirePackage{mathabx}
\RequirePackage{textgreek}
\RequirePackage[version=4]{mhchem}
\RequirePackage{amsthm}

% Formatting / section titles
\RequirePackage{titlesec}
\titleformat*{\section}{\Large\sffamily}
\titleformat*{\subsection}{\large\sffamily}
\titleformat*{\subsubsection}{\large\sffamily}

% Misc
\RequirePackage{setspace}
\RequirePackage{siunitx}
\RequirePackage{textcomp} % (note: can clash with degree symbol depending on other packages)
\RequirePackage{graphicx}
\RequirePackage{url}
\RequirePackage{color}
\RequirePackage{threeparttable}
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{makecell}
\RequirePackage[table]{xcolor}
\RequirePackage[framemethod=TikZ]{mdframed}
\RequirePackage{cancel}
\RequirePackage{comment}
\RequirePackage{enumitem}
\RequirePackage{wasysym}
\RequirePackage{listings}
\RequirePackage[colorlinks=true, urlcolor=blue, hyperfootnotes=false, hyperfigures=false, hyperindex=false, linkcolor=black]{hyperref}
\RequirePackage[font=small, margin=1cm]{caption}
\RequirePackage{float}

% Chemistry!
\RequirePackage{chemfig}

% Tables
\usepackage{hhline}
\usepackage{threeparttable}
\usepackage{multirow}

% =========================
% Layout settings (from your preamble)
% =========================
\setlength{\evensidemargin}{1.0cm}
\setlength{\oddsidemargin}{1.0cm}
\setlength{\topmargin}{-1.0cm}
\setlength{\textwidth}{14cm}
\setlength{\textheight}{22cm}
\setlength{\parskip}{2.5mm}

% Give more spacing in equation arrays
\setlength{\jot}{10pt}

% Allow page breaks in multiline equations
\allowdisplaybreaks

% =========================
% Table column types
% =========================
\newcolumntype{M}[1]{>{\centering\arraybackslash}m{#1}}
\newcolumntype{N}{@{}m{0pt}@{}}

% =========================
% Theorem / problem style
% =========================
\newtheoremstyle{break}% name
  {}% Space above
  {2em}% Space below
  {}% Body font
  {}% Indent amount
  {\bfseries}% Head font
  {.}% Punctuation after head
  {\newline}% Space after head
  {}% Head spec

\theoremstyle{break}
\newtheorem{problem}{Problem}

% Counters used by boxed envs
\newcounter{solution}
\newcounter{rubric}

% =========================
% mdframed boxes
% =========================
% Solution box
\mdfdefinestyle{solution}{%
    outerlinewidth=2pt,
    bottomline=false,
    leftline=false,rightline=false,
    topline=false,
    font=\small,%
    backgroundcolor=gray!20,%
    skipabove=-5em,
    skipbelow=\baselineskip,
    roundcorner=10pt,%
    innertopmargin=1em,%
    innerbottommargin=1em,%
    splittopskip=1em,%
    splitbottomskip=1em,%
    frametitle=\mbox{},
}
\newmdenv[%
    style=solution,
    settings={\global\refstepcounter{solution}},
    frametitlefont={\bfseries Solution~\thesolution\quad},
]{solution}

% Shaded box (same style as solution, but no counter stepping/title)
\newmdenv[style=solution]{shaded}

% Unshaded box
\mdfdefinestyle{unshaded}{%
    outerlinewidth=1pt,
    bottomline=true,
    leftline=true,rightline=true,
    topline=true,
    font=\small,%
    backgroundcolor=white,%
    skipabove=-5em,
    skipbelow=\baselineskip,
    roundcorner=10pt,%
    innertopmargin=1em,%
    innerbottommargin=1em,%
    splittopskip=1em,%
    splitbottomskip=1em,%
    frametitle=\mbox{},
}
\newmdenv[style=unshaded]{unshaded}

% Rubric box
\mdfdefinestyle{rubric}{%
    outerlinewidth=2pt,
    bottomline=false,
    leftline=false,rightline=false,
    topline=false,
    font=\small,%
    backgroundcolor=pink!20,%
    skipabove=-5em,
    skipbelow=\baselineskip,
    roundcorner=10pt,%
    innertopmargin=1em,%
    innerbottommargin=1em,%
    splittopskip=1em,%
    splitbottomskip=1em,%
    frametitle=\mbox{},
}
\newmdenv[%
    style=rubric,
    settings={\global\refstepcounter{rubric}},
    frametitlefont={\bfseries Rubric~\therubric\quad},
]{rubric}

% =========================
% Convenience commands
% =========================
\newcommand{\micron}{{\textmu}m}
\newcommand{\conc}[1]{c_{\mathrm{#1}}}

% =========================
% Numbering of problems, solutions, and equations
% =========================
\theoremstyle{break}
\numberwithin{problem}{section}
\numberwithin{solution}{section}
\numberwithin{equation}{section}

% =========================
% List formatting
% =========================
\setlist{itemsep=1pt}
\setitemize{listparindent=\parindent}
\setenumerate{listparindent=\parindent}

% =========================
% Listings configuration
% =========================
\definecolor{mygreen}{rgb}{0,0.6,0}
\definecolor{mygray}{rgb}{0.5,0.5,0.5}
\definecolor{mymauve}{rgb}{0.58,0,0.82}

\lstset{%
  backgroundcolor=\color{gray!20},
  basicstyle=\footnotesize\ttfamily,
  breakatwhitespace=false,
  breaklines=true,
  captionpos=t,
  commentstyle=\color{mygreen},
  deletekeywords={...},
  escapeinside={\%*}{*)},
  extendedchars=true,
  frame=single,
  keepspaces=true,
  keywordstyle=\color{blue},
  morekeywords={*,...},
  numbers=left,
  numbersep=5pt,
  numberstyle=\tiny\color{mygray},
  rulecolor=\color{black},
  showspaces=false,
  showstringspaces=false,
  showtabs=false,
  stepnumber=1,
  stringstyle=\color{mymauve},
  tabsize=2,
  title=\lstname
}

\endinput
