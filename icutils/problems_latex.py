import importlib
import pathlib
import shutil
import subprocess
import tempfile
import tomllib
import warnings

_texmfhome_cache = None


def _parse_latex_errors(log_file):
    """Extract error messages from LaTeX log file."""
    try:
        with open(log_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return ["Unable to read log file"]

    errors = []
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if line.startswith('!'):
            errors.append(line)
            if i + 1 < len(lines):
                errors.append(lines[i + 1])
            if i + 2 < len(lines) and lines[i + 2].strip():
                errors.append(lines[i + 2])

    if not errors:
        for line in lines:
            if 'error' in line.lower():
                errors.append(line)

    return errors if errors else ["Compilation failed but no specific errors found in log"]


def _compile_latex(compiler, tex_file_name, cwd=None):
    """Compile a LaTeX file. Returns True on success, raises RuntimeError on failure."""
    result = subprocess.run(
        [compiler, "-interaction=nonstopmode", tex_file_name],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log_file = pathlib.Path(tex_file_name).with_suffix('.log')
        if cwd:
            log_file = pathlib.Path(cwd) / log_file.name

        errors = _parse_latex_errors(log_file)
        error_msg = "LaTeX compilation failed:\n"
        error_msg += "\n".join(errors[:15])

        raise RuntimeError(error_msg)

    return True

def find_texmfhome() -> str:
    """Determine where the TEXMFHOME directory is. Result is cached."""
    global _texmfhome_cache
    if _texmfhome_cache is not None:
        return _texmfhome_cache

    if shutil.which("kpsewhich") is None:
        raise RuntimeError("Cannot use kpsewhich to get TEXMFHOME. Be sure integrated_core_problems.cls is available. ")

    try:
        texmfhome = subprocess.check_output(
            ["kpsewhich", "-var-value=TEXMFHOME"],
            text=True
        ).strip()
    except:
        raise RuntimeError("Unable to access TEXMFHOME. Be sure integrated_core_problems.cls is available.")

    # Get pathlib.Path object
    texmfhome = pathlib.Path(texmfhome).expanduser()

    # Create texmfhome if it is not already created
    texmfhome.mkdir(parents=True, exist_ok=True)

    _texmfhome_cache = texmfhome
    return texmfhome


def copy_cls(texmfhome=None, overwrite=False) -> None:
    """Copy the integrated_core_problems.cls file to TEXMFHOME."""
    if texmfhome is None:
        texmfhome = find_texmfhome()

    # Target directory. Must be TEXMFHOME/tex/latex/something-or-other/
    target_dir = texmfhome.joinpath('tex', 'latex', 'integrated_core_classes').expanduser()

    # Make the target directory if it does not already exist
    target_dir.mkdir(parents=True, exist_ok=True)

    cls_rel_path = 'data/integrated_core_problems.cls'
    target = pathlib.Path(target_dir) / pathlib.Path(cls_rel_path).name

    # Skip if file already exists and overwrite is False
    if target.exists() and not overwrite:
        return

    cls_file = importlib.resources.files('icutils').joinpath(*cls_rel_path.split('/'))

    if not cls_file.is_file():
        raise FileNotFoundError(f"File {cls_rel_path} not found in icutils package.")

    with importlib.resources.as_file(cls_file) as cls:
        shutil.copy2(cls, target)


def pdfproblem(problem, problem_bank_path, overwrite=True, compiler='pdflatex'):
    """Compile a single problem to a PDF document."""
    # Just problem name, not .tex
    if problem.endswith(".tex"):
        problem = problem[:-4]

    # Make sure IC problems class is loaded
    print("Verifying TeX tools...")
    copy_cls(texmfhome=None, overwrite=False)

    # Convert problem bank path to pathlib object
    problem_bank_path = pathlib.Path(problem_bank_path).expanduser().resolve()

    # Get figs directory
    figs_path = problem_bank_path.joinpath('figs')

    # Get code directory
    code_path = problem_bank_path.joinpath('code')

    # Path to the TeX file
    tex_file = problem_bank_path.joinpath(problem + '.tex')    

    # Make sure the TeX file exists
    if not tex_file.exists():
        raise FileNotFoundError(f"File {tex_file} does not exist.")

    preamble_text = """\\documentclass{integrated_core_problems}
    
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This is where we define whether or not we will show the solutions
% when we compile.  Use \\excludecomment{answerkey} to hide solutions.
\\includecomment{answerkey}
\\includecomment{extracomment}
\\excludecomment{answerspaces}
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\begin{document}

% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\\renewcommand{\\thesection}{0}
\\setcounter{problem}{-1}
\\setcounter{solution}{0}
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
"""

    # Read in the problem text
    with open(tex_file, 'r') as f:
        problem_text = f.read()

    # Only get the problem and solution
    end_ind = problem_text.find('\\end{document}')
    if end_ind == -1:
        problem_text = problem_text[problem_text.find('\\begin{problem}'):]
    else:
        problem_text = problem_text[problem_text.find('\\begin{problem}'):end_ind]

    # Substitute in full path of figures
    problem_text = problem_text.replace('{figs/', '{' + figs_path.as_posix() + '/')

    # Substitute in full path of code
    problem_text = problem_text.replace('{code/', '{' + code_path.as_posix() + '/')

    # Check for the output PDF
    pdf_file = pathlib.Path(problem + '.pdf')

    if pdf_file.exists() and not overwrite:
        raise FileExistsError(f"{pdf_file} already exists. Use `overwrite=True` kwarg to overwrite.")

    with tempfile.TemporaryDirectory() as tmp:
        # Make temporary TeX file
        tmp = pathlib.Path(tmp)
        tmp_tex_file = tmp / pathlib.Path(problem + '.tex')
        tex_source = preamble_text + problem_text + '\n\\end{document}\n'
        tmp_tex_file.write_text(tex_source)

        # Compile twice in temporary directory
        print("Building TeX document...")
        for _ in range(2):
            try:
                _compile_latex(compiler, tmp_tex_file.name, cwd=tmp)
            except RuntimeError as e:
                raise RuntimeError(f"Error compiling problem '{problem}':\n{str(e)}")

        # Copy result to pwd
        shutil.copy2(tmp / pathlib.Path(problem + '.pdf'), pdf_file)

    print(f"Build successful, output PDF file is: {pdf_file}")
    

def check_hw_spec(spec):
    """Checks a homework specification for all fields."""
    # Necessary fields for header
    for key in ['course', 'term', 'year', 'number', 'due_time', 'problem']:
        if key not in spec.keys():
            raise RuntimeError(f"'{key}' field not in specification.")

    # Make sure problems are a list
    if type(spec['problem']) != list:
        raise RuntimeError('Problems must be entered as array of tables as `[[problem]]` in the TOML specification.')
    
    total_points = 0
    names = []
    for prob in spec['problem']:
        if type(prob) != dict:
            raise RuntimeError('Problems must be entered as array of tables as `[[problem]]` in the TOML specification.')
        if 'name' not in prob.keys():
            raise RuntimeError('Every problem must have a `name` field.')
        if 'points' not in prob.keys():
            raise RuntimeError('Every problem must have a `points` field.')
        if 'subjects' not in prob.keys():
            warnings.warn(f"No 'subjects' field for problem {prob['name']}.", UserWarning)
        if prob['name'] in names:
            raise RuntimeError(f'Problem {prob['name']} is used more than once.')
        names.append(prob['name'])
        total_points += int(prob['points'])

    if total_points != 100:
        warnings.warn('Points do not add to 100.', RuntimeWarning)


def _add_points(problem_text, points):
    """Add point total to a problem name
    """
    start = problem_text.find(r"\begin{problem}")
    if start == -1:
        raise ValueError(r"'\begin{problem}' not found")

    # Search for first ']' AFTER the marker
    idx = problem_text.find("]", start + len(r"\begin{problem}"))
    if idx == -1:
        raise ValueError("No ']' found after '\\begin{problem}'")

    return problem_text[:idx] + f', {points} points]' + problem_text[idx+1:]


def _add_subjects(problem_text, subjects):
    """Add subjects to problem text.
    """
    if subjects is None or len(subjects) == 0:
        return problem_text

    start = problem_text.find(r"\begin{problem}")
    if start == -1:
        raise ValueError(r"'\begin{problem}' not found")

    # Search for first ']' AFTER \begin{problem}
    bracket_idx = problem_text.find("]", start + len(r"\begin{problem}"))
    if bracket_idx == -1:
        raise ValueError("No ']' found after '\\begin{problem}'")

    # Move to the start of the line after ']'
    pos = problem_text.find("\n", bracket_idx)
    pos = pos + 1 if pos != -1 else len(problem_text)

    # Skip \label{...} and %comment lines
    while pos < len(problem_text):
        line_end = problem_text.find("\n", pos)
        line = problem_text[pos:line_end] if line_end != -1 else problem_text[pos:]
        stripped = line.strip()
        if stripped.startswith(r"\label{") or stripped.startswith("%"):
            pos = line_end + 1 if line_end != -1 else len(problem_text)
        else:
            break

    subjects = [s.capitalize() for s in subjects]

    if len(subjects) == 1:
        subjects_text = "\n" + r"\noindent \textit{Subject: "
        subjects_text += subjects[0] + '.'
        subjects_text += r"}" + "\n\n" + r"\noindent "
    else:
        subjects_text = "\n" + r"\noindent \textit{Subjects: "
        for subject in subjects[:-1]:
            subjects_text += subject + ", "
        subjects_text += subjects[-1] + '.'
        subjects_text += r"}" + "\n\n" + r"\noindent "

    return problem_text[:pos] + subjects_text + problem_text[pos:].lstrip()


def pdfset(toml_spec, problem_bank_path, overwrite=True, compiler='pdflatex'):
    """Compile problems in a TOML specification into a PDF document."""
    # Infer .toml suffix if not given
    toml_spec = pathlib.Path(toml_spec)
    if toml_spec.suffix != '.toml':
        toml_spec = toml_spec.with_name(toml_spec.name + '.toml')

    # Load in specification and check it
    with open(toml_spec, 'rb') as f:
        spec = tomllib.load(f)
    check_hw_spec(spec)

    if 'include_time_to_completion_problem' in spec.keys():
        include_time_to_completion_problem = spec['include_time_to_completion_problem']
    else:
        include_time_to_completion_problem = False

    # Make sure IC problems class is loaded
    print("Verifying TeX tools...")
    copy_cls(texmfhome=None, overwrite=False)

    # Convert problem bank path to pathlib object
    problem_bank_path = pathlib.Path(problem_bank_path).expanduser().resolve()

    # Get figs directory
    figs_path = problem_bank_path.joinpath('figs')

    # Get code directory
    code_path = problem_bank_path.joinpath('code')
    
    preamble_text = """\\documentclass{integrated_core_problems}
    
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This is where we define whether or not we will show the solutions
% when we compile.  Use \\excludecomment{answerkey} to hide solutions.
\\includecomment{answerkey}
\\includecomment{extracomment}
\\excludecomment{answerspaces}
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\begin{document}

% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\\renewcommand{\\thesection}{0}
\\setcounter{problem}{0}
\\setcounter{solution}{0}
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
""".replace("{\\thesection}{0}", "{\\thesection}{" + str(spec['number']) + "}")
    
    if include_time_to_completion_problem:
        preamble_text = preamble_text.replace('\\setcounter{problem}{0}', '\\setcounter{problem}{-1}')

    preamble_text += f"\\centerline{{\\textbf{{{spec['course']}, {spec['term'].capitalize()} {spec['year']}}}}}\n"
    preamble_text += f"\\centerline{{\\textbf{{Homework {spec['number']}}}}}\n"
    preamble_text += f"\\centerline{{Due at {spec['due_time']}}}\n"
    preamble_text += "\\reversemarginpar\n\\marginparsep  0.1in\n\\marginparwidth 0.7in\n\n"
    preamble_text += "% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"

    # Add problems
    problems_text = ""

    if include_time_to_completion_problem:
        problems_text += """% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\\begin{problem}[Time to completion, 0 points]
\\label{prob:time_to_completion}
Write down how many hours you spent working on this problem set.
\\end{problem}

"""
    for prob in spec['problem']:
        # Just problem name, not .tex
        if prob['name'].endswith(".tex"):
            problem = prob['name'][:-4]
        else:
            problem = prob['name']

        # Path to the TeX file
        tex_file = problem_bank_path.joinpath(problem + '.tex')    

        # Make sure the TeX file exists
        if not tex_file.exists():
            raise FileNotFoundError(f"File {tex_file} does not exist.")

        # Read in the problem text
        with open(tex_file, 'r') as f:
            prob_text = f.read()

        # Only get the problem and solution
        end_ind = prob_text.find('\\end{document}')
        if end_ind == -1:
            prob_text = prob_text[prob_text.find('\\begin{problem}'):]
        else:
            prob_text = prob_text[prob_text.find('\\begin{problem}'):end_ind]

        # Put in the point total
        prob_text = _add_points(prob_text, int(prob['points']))

        # Put in the subjects
        prob_text = _add_subjects(prob_text, prob.get('subjects', []))

        # Add the problem text to the main document text
        problems_text += "\n\n% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        problems_text += prob_text

    # Substitute in full path of figures
    problems_text = problems_text.replace('{figs/', '{' + figs_path.as_posix() + '/')

    # Substitute in full path of code
    problems_text = problems_text.replace('{code/', '{' + code_path.as_posix() + '/')

    # Prefix for homework files, taken from the TOML file name
    prefix = toml_spec.stem

    # Make a TeX file
    set_tex_file = pathlib.Path(prefix + ".tex")

    if set_tex_file.exists() and not overwrite:
        raise FileExistsError(f"{set_tex_file} already exists. Use `overwrite=True` kwarg to overwrite.")

    tex_source = preamble_text + problems_text + '\n\\end{document}\n'
    set_tex_file.write_text(tex_source)

    solution_pdf = pathlib.Path(prefix + '_solution.pdf')
    regular_pdf = pathlib.Path(prefix + '.pdf')

    # Compile in a temporary directory so auxiliary files do not end up in pwd
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        tmp_tex_file = tmp / set_tex_file.name

        # Compile twice with solutions
        print("Building TeX document (with solutions)...")
        tmp_tex_file.write_text(tex_source)
        for _ in range(2):
            _compile_latex(compiler, tmp_tex_file.name, cwd=tmp)

        # Copy result with solutions
        shutil.copy2(tmp / regular_pdf.name, solution_pdf)

        # Now compile without solutions
        print("Building TeX document (without solutions)...")
        tex_source = tex_source.replace('includecomment', 'excludecomment')
        tmp_tex_file.write_text(tex_source)
        for _ in range(2):
            _compile_latex(compiler, tmp_tex_file.name, cwd=tmp)

        # Copy result without solutions
        shutil.copy2(tmp / regular_pdf.name, regular_pdf)

    set_tex_file.write_text(tex_source)
    print(f"Build successful, output PDF files are: {regular_pdf} and {solution_pdf}")
