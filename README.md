# icutils

Utilities for Integrated Core

This package contains a set of utilities for administration of Caltech's Integrated Core curriculum. Included is functionality for grading and building of problem sets. This is specific to materials that are *not* public, so this is of essentially no use for anyone outside of the Integrated Core faculty and staff.

## Installation

Clone the repository and install with [pixi](https://pixi.sh):

```bash
git clone https://github.com/justinbois/icutils.git
cd icutils
pixi install
```

## Usage

`icutils` provides to basic functionalities: grading analysis and problem set building. The former is through wrangling of grading spreadsheets and the latter is through a command line interface that builds TeX files from problems in the problem bank.

### Grading analysis

Examples of grading analysis are shown in the `examples/example_grade_analysis.ipynb` notebook.


### Homework and exam generation

The `icutils` command line interface provides two commands for compiling LaTeX problems into PDFs: `pdfproblem` and `pdfset`. Both look for `.tex` files in a problem bank directory, resolved in this order:

1. The `--problem-bank-path` flag, if provided.
2. The `ICPROBLEMBANKPATH` environment variable.
3. The current working directory.

#### `pdfproblem`

Compile a single problem to a PDF in the current directory.

```bash
icutils pdfproblem PROBLEM_NAME [OPTIONS]
```

**Arguments:**
- `PROBLEM_NAME` — Name of the problem (without the `.tex` extension).

**Options:**
- `--problem-bank-path PATH` — Path to the problem bank directory.
- `--overwrite / --no-overwrite` — Overwrite an existing output PDF (default: `--overwrite`).
- `--compiler COMPILER` — LaTeX compiler to use, e.g., `pdflatex`, `xelatex`, `lualatex` (default: `pdflatex`).

**Example:**

```bash
icutils pdfproblem space_curves_and_dna --problem-bank-path ~/problem_bank
```

#### `pdfset`

Compile a set of problems, defined in a TOML specification file, into a single PDF in the current directory.

```bash
icutils pdfset TOML_SPEC [OPTIONS]
```

**Arguments:**
- `TOML_SPEC` — Path to the TOML file specifying the problem set.

**Options:**
- `--problem-bank-path PATH` — Path to the problem bank directory.
- `--overwrite / --no-overwrite` — Overwrite an existing output PDF (default: `--overwrite`).
- `--compiler COMPILER` — LaTeX compiler to use, e.g., `pdflatex`, `xelatex`, `lualatex` (default: `pdflatex`).

**Example TOML spec** (see `examples/sample_homework.toml`):

```toml
course = 'Integrated Core'
term = 'Winter'
year = '2026'
number = '2c'
due_time = '11:59 PST, Friday, January 16, 2026'

include_time_to_completion_problem = true

[[problem]]
name = 'rain_cloud_distance'
points = 20

[[problem]]
name = 'space_curves_and_dna'
points = 80
```

**Example:**

```bash
icutils pdfset sample_homework.toml --problem-bank-path ~/Box/integrated_core/problem_bank
```

