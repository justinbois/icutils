import csv
import io
import pathlib
import typing

import pandas as pd
import polars as pl

def wrangle(
    gradesheet: typing.Optional[str] = None,
    late_multiplier: typing.Optional[str] = None,
    engagement: typing.Optional[str] = None,
    homework_nulls_to_zero: bool = True,
    df_software: str = 'polars',
    n_students: typing.Optional[int] = None,
    n_rows: typing.Optional[int] = None,
    omit_students: typing.Optional[typing.Union[str, typing.List[str], typing.Tuple[str, ...]]] = None,
) -> typing.Union[pd.DataFrame, pl.DataFrame]:
    """Wrangle grading data into tall tidy format.

    Parameters
    ----------
    gradesheet : str
        Path to gradesheet CSV file. Default is 
        "integrated_core_concepts_and_topics - gradesheet.csv", which
        is what the name would be if you exported the gradesheet as a
        CSV to the working directory.
    late_multipler : str
        Path to late multiplier CSV file. Default is 
        "integrated_core_concepts_and_topics - late_multiplier.csv", 
        which is what the name would be if you exported the late 
        multiplier sheet as a CSV to the working directory.
    engagement : str
        Path to engagement CSV file. Default is 
        "integrated_core_concepts_and_topics - engagement.csv", which
        is what the name would be if you exported the engagement sheet
        as a CSV to the working directory.
    homework_nulls_to_zero : bool, default True
        If True, convert all nulls in homework score fields to zero.
        If False, leave as nulls.
    df_software : str, default 'polars'
        Either 'polars' or 'pandas' for either Polars or Pandas output
        data frame.
    n_students : int, default None
        Number of students. This is useful in case course staff adds
        spurious columns to the gradesheet to do in-Google-Docs 
        analysis. In None, inferred from the late_penalty sheet,
        which is assumed not to have any spurious columns
    n_rows : int, default None
        Number of rows in the gradesheet to be read, including the
        header row. If None, all rows are read in. If course staff
        have added spurious rows to the gradesheet to do in-Google-
        Docs analysis, this will fail, possibly silently, unless 
        n_rows is explicitly set.
    omit_student : list of str
        List of students to be omitted from the analysis.

    Returns
    -------
    output : Polars or Pandas data frame
        Tall data frame containing grades. Each row of the data frame
        contains a problem. The columns of the data frame are:
            - term: Entries are 'fall', 'winter', and 'spring'
            - assignment: Name of assignment, like '3a' for a homework,
              or 'midterm' for the midterm exam
            - assignment_type: Entries are 'homework', 'midterm', 
              'final', 'rfp', and 'engagement'
            - problem: Problem number
            - points: Number of points possible for the problem
            - counts toward grade: Entries are either True or False
            - subject 1: Primary subject of the assignment. Entries are
              'physics', 'math', 'chemistry', 'biology', 'geology', or
              'humanities'. May be left blank.
            - subject 2: Secondary subject of the assignment. Same
              possible entries as above. May be left blank.
            - subject 3: Tertiary subject of the assignment. Same
              possible entries as above. May be left blank.
            - lab: True if the problem was associated with a lab and
              False otherwise. null if unknown.
            - grader: Name of grade in format 'lastname, firstname'. 
              For multiple graders, names are separated with semicolons.
            - student: Student name
            - score: Score student achieved on assignment. The only
              exceptions are problems numbered 0, in which this column
              contains the number of hours the student spend on the
              assignment.
            - late_multiplier: Multiplier of score based on lateness of
              assignment submission. Possible values are 0, 0.5, and 1.

    Notes
    -----
    .. We could automatically fetch the spreadsheet data using Google's
       API. I do not want to do this because I do not want access keys
       being shared.
    .. When people mess with the format of the spreadsheet, Polars 
       cannot simply read it in. In particular, adding analysis rows
       or columns will mess up schemas. We cannot just use the n_rows
       kwarg of `pl.read_csv()` because if the CSV file is in Dropbox,
       the whole file needs to be read anyway because it's under remote
       storage which does not support partial reads. Instead, we use
       the csv package to make a new CSV file with just the entries
       we will use.
    """
    # Get default data sets
    if gradesheet is None:
        gradesheet = 'integrated_core_concepts_and_topics - gradesheet.csv'
    if late_multiplier is None:
        late_multiplier = 'integrated_core_concepts_and_topics - late_multiplier.csv'
    if engagement is None:
        engagement = 'integrated_core_concepts_and_topics - engagement.csv'

    # Make sure data sets exist
    for fname in [gradesheet, late_multiplier, engagement]:
        if not pathlib.Path(fname).is_file():
            raise RuntimeError(f"{fname} is either missing or not a file.")

    # Check input for software
    if df_software.lower() == 'polars':
        df_software = 'polars'
    elif df_software.lower() == 'pandas':
        df_software = 'pandas'
    else:
        raise RuntimeError("Invalid input for `df_software`.")

    # Read in late multiplier and get the number of students
    if n_students is None:
        df_late = pl.read_csv(late_multiplier)
        n_students = df_late.width - 2
    else:
        with open(late_multiplier, newline='') as f:
            reader = csv.reader(f, delimiter=',')
            iostr = ''
            for row in reader:
                # First two columns are term, assignment
                iostr += '\t'.join(row[:n_students + 2]) + '\n'

        df_late = pl.read_csv(io.StringIO(iostr), separator='\t')

    # Read in enagement
    with open(engagement, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        iostr = ''
        for row in reader:
            # First three columns are term, assignment, points
            iostr += '\t'.join(row[:n_students + 3]) + '\n'
    
    df_engagement = pl.read_csv(io.StringIO(iostr), separator='\t')

    # Read in grade sheet
    # First ten columns are metadata: term, assignment, problem, points, 
    # counts toward grade, subject 1, subject 2, subject 3, due date, grader, lab
    with open(gradesheet, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        row_count = 0
        iostr = ''
        for row in reader:
            iostr += '\t'.join(row[:n_students+11]) + '\n'
            row_count += 1
            if row_count == n_rows:
                break

    df = pl.read_csv(
        io.StringIO(iostr), 
        separator='\t', 
        null_values=["null", "Null"], 
        try_parse_dates=True
    )

    # Add a column for assignment type
    df = df.with_columns(
        pl.when(pl.col("assignment").str.contains("midterm"))
        .then(pl.lit("midterm"))
        .when(pl.col("assignment").str.contains("final"))
        .then(pl.lit("final"))
        .when(pl.col("assignment").str.contains("rfp"))
        .then(pl.lit("rfp"))
        .otherwise(pl.lit("homework"))
        .alias("assignment_type")
    )

    # Add pertinent columns to engagement
    df_engagement = df_engagement.with_columns(
        pl.lit("engagement").alias("assignment_type"),
        pl.lit(True).alias("counts toward grade"),
    )

    # Add engagement grades
    df = pl.concat([df, df_engagement], how="diagonal_relaxed")

    # Make the data frame tall, where each row is a single student's
    # performance on a single problem
    df = df.unpivot(
        index=[
            "term",
            "assignment",
            "assignment_type",
            "problem",
            "points",
            "counts toward grade",
            "subject 1",
            "subject 2",
            "subject 3",
            "lab",
            "due date",
            "grader",
        ],
        variable_name="student",
        value_name="score",
    )

    # Convert unsubmitted (null) scores to zero
    if homework_nulls_to_zero:
        df = df.with_columns(pl.col("score").fill_null(0))

    # Make late homework data frame tall
    df_late = df_late.unpivot(
        index=["term", "assignment"],
        variable_name="student",
        value_name="late_multiplier",
    )

    # Join the data frames
    df = df.join(df_late, on=["term", "assignment", "student"], how="left")

    # Convert unentered late penalties to one
    df = df.with_columns(pl.col("late_multiplier").fill_null(1))

    # Convert everything except names to lower case
    df = df.with_columns(
        pl.col("term").str.to_lowercase(),
        pl.col("assignment").str.to_lowercase(),
        pl.col("grader").str.to_lowercase(),
        pl.col("subject 1").str.to_lowercase(),
        pl.col("subject 2").str.to_lowercase(),
        pl.col("subject 3").str.to_lowercase(),
    )

    # Eliminate all spaces from entries in term, assignment, and subject fields
    df = df.with_columns(
        pl.col('term', 'assignment', 'subject 1', 'subject 2', 'subject 3').str.replace_all(r"\s+", "")
    )

    # Filter out students who are not included
    if type(omit_students) == str:
        omit_students = [omit_students]
    df = df.filter(~pl.col('student').is_in(omit_students))

    # Convert to Pandas if desired
    if df_software == 'pandas':
        df = df.to_pandas()

    return df


def drop_lowest_hw(
    df: typing.Union[pd.DataFrame, pl.DataFrame]
) -> typing.Union[pd.DataFrame, pl.DataFrame]:
    """Return a data frame with the lowest score for each variety of 
    homework (a, b, c) dropped.

    Parameters
    ----------
    df : Polars or Pandas data frame
        Data frame loaded using `icgrade.wrangle()`

    Returns
    -------
    output : Polars or Pandas data frame
        Data frame with each student's lowest score for each variety
        of homework (a, b, c) dropped.
    """
    if type(df) == pd.DataFrame:
        df_software = 'pandas'
        df = pl.from_pandas(df)
    else:
        df_software = 'polars'

    # Compute lowest scores on each assignment class (a, b, c, abc)
    lowscores_df = (
        df
        .sort(by=['student', 'assignment', 'problem'])
        .filter(
            (pl.col('assignment_type') == 'homework')
            & (~pl.col('assignment').str.contains('lab', literal=True))
            & (pl.col('counts toward grade'))
        )
        .group_by(['student', 'assignment'], maintain_order=True)
        .agg((pl.col('score') * pl.col('late_multiplier')).sum() / pl.col('points').sum())
        .with_columns(pl.col('assignment').str.slice(1, None).alias('assignment_class'))
        .group_by(['student', 'assignment_class'], maintain_order=True)
        .agg(pl.all().bottom_k_by(by='score', k=1))
        .explode(pl.col('assignment', 'score'))
        .sort(by=['student', 'assignment'])
    )

    # Determine drops. If abc is the global lowest, drop it. If abc is not the global 
    # lowest, keep it and drop only the lowest assignments in the a, b, and c categories 
    # that are lower than it.
    drops = {}
    for (student,), sub_df in lowscores_df.group_by("student", maintain_order=True):
        abc_score = sub_df.filter(pl.col("assignment_class") == "abc")["score"].item()
        low_score = sub_df["score"].min()
        if abc_score == low_score:
            drops[student] = [
                sub_df.filter(pl.col("assignment_class") == "abc")["assignment"].item()
            ]
        else:
            drops[student] = [
                row["assignment"]
                for row in sub_df.filter(pl.col("assignment_class") != "abc").iter_rows(
                    named=True
                )
                if row['score'] < abc_score
            ]

    # Filter the data set for the lowest drops
    filters = [
        (pl.col("student") == student) & pl.col("assignment").is_in(assignments)
        for student, assignments in drops.items()
    ]

    df = df.filter(~pl.any_horizontal(filters))

    if df_software == 'pandas':
        df = df.to_pandas()

    return df
