import os
import pathlib
import click

from .problems_latex import *

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """Utilities for Integrated Core problem workflows."""
    pass


def resolve_problem_bank_path(flag_value: str | None) -> pathlib.Path:
    """Resolve problem bank path with priority:
       1) CLI flag
       2) ICPROBLEMBANKPATH env var
       3) current working directory
    """
    if flag_value is not None:
        path = flag_value
    elif "ICPROBLEMBANKPATH" in os.environ:
        path = os.environ["ICPROBLEMBANKPATH"]
    else:
        path = os.getcwd()

    return pathlib.Path(path).expanduser().resolve()

@cli.command("pdfproblem")
@click.argument("problem", type=str)
@click.option(
    "--problem-bank-path",
    "problem_bank_path",
    default=None,
    type=click.Path(path_type=str),
    help="Path to the problem bank directory. If the flag is not given, uses ICPROBLEMBANKPATH environment variable. If ICPROBLEMBANKPATH is not set, defaults to pwd.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite existing output PDF in the current directory.",
)
def pdfproblem_cmd(problem: str, problem_bank_path: str, overwrite: bool) -> None:
    """Compile a single problem to a PDF in the current directory."""
    try:
        resolved_path = resolve_problem_bank_path(problem_bank_path)
        pdfproblem(problem, resolved_path, overwrite=overwrite)
    except Exception as e:
        if "does not exist." in str(e):
            raise click.ClickException(str(e) + " You may need to provide the problem bank path using the --problem-bank-path flag.") from e
        else:
            raise click.ClickException(str(e)) from e


@cli.command("pdfset")
@click.argument("toml_spec", type=str)
@click.option(
    "--problem-bank-path",
    "problem_bank_path",
    default=None,
    type=click.Path(path_type=str),
    help="Path to the problem bank directory. If the flag is not given, uses ICPROBLEMBANKPATH environment variable. If ICPROBLEMBANKPATH is not set, defaults to pwd.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite existing output PDF in the current directory.",
)
def pdfset_cmd(toml_spec: str, problem_bank_path: str, overwrite: bool) -> None:
    """Compile a single problem to a PDF in the current directory."""
    try:
        resolved_path = resolve_problem_bank_path(problem_bank_path)
        pdfset(toml_spec, resolved_path, overwrite=overwrite)
    except Exception as e:
        if "does not exist." in str(e):
            raise click.ClickException(str(e) + " You may need to provide the problem bank path using the --problem-bank-path flag.") from e
        else:
            raise click.ClickException(str(e)) from e


def main() -> None:
    cli(prog_name="icutils")


if __name__ == "__main__":
    main()
