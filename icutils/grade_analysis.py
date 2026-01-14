import typing

import pandas as pd
import polars as pl

import iqplot

import bokeh.io
import bokeh.layouts
import bokeh.resources

def subject_scores(
    df: typing.Union[pd.DataFrame, pl.DataFrame],
    subject: typing.Literal['math', 'physics', 'chemistry', 'biology', 'geology', 'humanities'],
    term: typing.Literal['fall', 'winter', 'spring', 'summer'],
    level: int = 3,
    homework_weight: typing.Union[float, int] = 0.4,
    midterm_weight: typing.Union[float, int] = 0.2,
    final_weight: typing.Union[float, int] = 0.3,
    engagement_weight: typing.Union[float, int] = 0.2,
    engagement_weeks: int = 10,
):
    """
    Compute a table of student scores in a subject for a term.

    Parameters
    ----------
    df : Polars or Pandas DataFrame
        Data frame acquired using `icgrade.wrangle()`.
    subject : str
        One of 'math', 'physics', 'chemistry', 'biology', 'geology', 
        'humanities'.
    term : str, one of 'fall', 'winter', 'spring', or 'summer'
        Term of the assignment
    level : int, default 3
        Which "level" to consider for the subject to count toward the
        grade. For example, if a problem has listed subjects 'physics',
        'math', and 'chemistry' and `level` is 2, then the problem 
        counts toward physics and math, but not chemistry.
    homework_weight : float, default 0.4
        Weight to assign homework percentage in final grade.
    midterm_weight : float, default 0.2
        Weight to assign midterm exam percentage in final grade.
    final_weight : float, default 0.3
        Weight to assign final exam percentage in final grade.
    engagement_weight : float, default 0.3
        Weight to assign engagement percentage in final grade.
    engagement_weeks : int, default 10
        Number of weeks to consider in engagement score.

    Returns
    -------
    output : Polars or Pandas data frame
        Data frame containing total percentages for the term. Each row
        corresponds to a single student's score. The columns are, with
        all percentages given as numbers between zero and one,
            - student: The name of the student.
            - homework: Homework percentage.
            - midterm: Midterm exam percentage.
            - final: Final exam percentage.
            - engagement: Engagement percentage
        Note that columns are missing if their respective weights are
        zero.
    """
    if type(df) == pd.core.frame.DataFrame:
        input_format = 'pandas'
        df = pl.from_pandas(df)
    else:
        input_format = 'polars'

    if level not in (1, 2, 3):
        raise RuntimeError('Invalid level. Must be 1, 2, or 3.')
    
    if term not in ('fall', 'winter', 'spring'):
        raise RuntimeError("`term` must be  one of 'fall', 'winter', or 'spring'.")

    # Fill in dummy columns for missing ones
    if 'engagement' not in df['assignment_type']:
        if engagement_weight > 0:
            raise RuntimeError(
                'engagement_weight > 0, but there are no engagement grades.'
            )

    if 'homework' not in df['assignment_type']:
        if homework_weight > 0:
            raise RuntimeError(
                'homework_weight > 0, but there are no homework grades.'
            )

    if 'midterm' not in df['assignment_type']:
        if midterm_weight > 0:
            raise RuntimeError(
                'midterm_weight > 0, but there are no midterm grades.'
            )

    if 'final' not in df['assignment_type']:
        if final_weight > 0:
            raise RuntimeError(
                'final_weight > 0, but there are no final grades.'
            )

    if level == 1:
        subject_condition = pl.col('subject 1') == subject
    elif level == 2:
        subject_condition = (
            (pl.col('subject 1') == subject)
            | (pl.col('subject 2') == subject)
        )
    else:
        subject_condition = (
            (pl.col('subject 1') == subject)
            | (pl.col('subject 2') == subject)
            | (pl.col('subject 3') == subject)
        )

    engagement_condition = (
        (pl.col('assignment_type') == 'engagement')
        & (pl.col('assignment') <= 'week_{0:02d}'.format(engagement_weeks))
    )

    filter_conditions = (
        (pl.col('term') == term)
        & (pl.col('counts toward grade'))
        & (subject_condition | engagement_condition)
    )

    percent_calculator = (
        (pl.col("score") * pl.col("late_multiplier")).sum() / pl.col("points").sum()
    )

    total_weight = (
        homework_weight 
        + midterm_weight 
        + final_weight 
        + engagement_weight
    )    
    score_calculator = 0.0
    for weight, col in zip(
        [homework_weight, midterm_weight, final_weight, engagement_weight],
        ['homework', 'midterm', 'final', 'engagement']):
        if weight > 0:
            score_calculator += weight * pl.col(col)
    score_calculator /= total_weight

    df_out = (
        df
        .filter(filter_conditions)
        .group_by(['student', 'assignment_type'], maintain_order=True)
        .agg(percent_calculator)
        .pivot(on='assignment_type', values='score')
        .with_columns((score_calculator).alias('total'))
        .sort(by='student')
    )

    if input_format == 'pandas':
        return df_out.to_pandas()
    
    return df_out


def assignment_dashboard(
    df: typing.Union[pd.DataFrame, pl.DataFrame],
    term: typing.Literal['fall', 'winter', 'spring', 'summer'],
    assignment: str,
    output_file: typing.Optional[str] = None,
    title: str = 'IC scores',
):
    """Build a dashboard with scores and plot for a single assignment.

    Parameters
    ----------
    df : Polars or Pandas DataFrame
        Data frame acquired using `icgrade.wrangle()`.
    term : str, one of 'fall', 'winter', 'spring', or 'summer'
        Term of the assignment
    assignment : str
        Name of assignment, e.g., '3b' or 'midterm_1c'
    output_file : str, default None
        Name of file to write the dashboard to. If not given,
        written to term_assignment_scores.html
    title : str, default 'IC scores'
        Title of HTML file

    Returns
    -------
    Nothing is returned. An HTML file containing the dashboard is 
    written to `output_file`.
    """
    if type(df) == pd.core.frame.DataFrame:
        df = pl.from_pandas(df)

    if output_file is None:
        output_file = f'{term}_{assignment}_scores.html'.replace(' ', '_')

    if not df['term'].is_in([term]).any():
        raise RuntimeError(f"term '{term}' is not in the data frame.")

    if not df['assignment'].is_in([assignment]).any():
        raise RuntimeError(f"assignment '{assignment}' is not in the data frame.")

    # Filter what we want
    df = (
        df
        .filter(
            (pl.col('term') == term) 
            & (pl.col('assignment') == assignment) 
            & (pl.col('counts toward grade') == True)
        )
        .select(pl.col('problem', 'score', 'points', 'student'))
        .with_columns(
            pl.col('problem').cast(str),
            pl.format("{} / {}", pl.col("score").cast(int), pl.col("points")).alias("score_string")
        )
    )

    # Get total score
    df_total = (
        df
        .select(pl.col('student', 'score'))
        .group_by('student')
        .sum()
        .sort(by=['score', 'student'], descending=True)
    )
    df_total = df_total.with_columns(
        pl.lit('total').alias('problem'),
        pl.lit(100).alias('points')
    )
    df_total = df_total.with_columns(
        pl.format("{}/{}", pl.col("score").cast(int), pl.col("points")).alias("score_string")
    )

    df = pl.concat((df, df_total), how='diagonal_relaxed')

    # Get scores as a percent
    df = df.with_columns(
        (100 * pl.col('score') / pl.col('points')).alias('score_percent')
    )

    # Build table
    cds_table = bokeh.models.ColumnDataSource(df_total.select(pl.col('student', 'score')))
    columns = [
        bokeh.models.TableColumn(field="student", title="student"),
        bokeh.models.TableColumn(field="score", title="score"),
    ]
    table = bokeh.models.DataTable(
        source=cds_table,
        columns=columns,
        index_position=None,
        width=250,
        height=450,
        row_height=24,
        selectable=True,
        reorderable=True,
    )

    p = iqplot.strip(
        data=df,
        q='score_percent',
        cats='problem',
        tooltips=[('student', '@student'), ('score', '@score_string')],
        spread='swarm',
        x_axis_label='score (%)',
        y_axis_label='problem',
        frame_height=375,
    )

    # Add transparency and size
    cds = p.renderers[0].data_source
    cds.data['alpha'] = [1.0] * len(cds.data['problem'])
    cds.data['size'] = [4] * len(cds.data['problem'])

    # Update glyphs
    p.renderers[0].glyph.fill_alpha = 'alpha'
    p.renderers[0].glyph.line_alpha = 'alpha'
    p.renderers[0].glyph.size = 'size'

    # JavaScript callback
    callback = bokeh.models.CustomJS(args=dict(cds=cds, cds_table=cds_table), code="""
    const students = cds.data['student'];
    const selected_indices = cds_table.selected.indices;
    const alpha = cds.data['alpha'];
    const size = cds.data['size'];

    // Determine which students are selected in the table
    let selected_students = [];
    for (let i = 0; i < selected_indices.length; i++) {
        selected_students.push(cds_table.data['student'][selected_indices[i]]);
    }

    console.log(cds_table.selected.indices);
    console.log(cds_table.data);

    for (let i = 0; i < students.length; i++) {
        if (selected_students.length === 0 || selected_students.includes(students[i])) {
            alpha[i] = 1.0;
            size[i] = (selected_students.length === 1) ? 7 : 4;
        }
        else {
            alpha[i] = 0.1;
            size[i] = 4;
        }
    }

    cds.change.emit();
    """)

    cds_table.selected.js_on_change("indices", callback)

    # Make the layout and save
    layout = bokeh.layouts.row(p, bokeh.models.Spacer(width=25), table)
    bokeh.io.save(layout, output_file, title=title, resources=bokeh.resources.CDN)

    print(f'Dashboard saved to {output_file}.')

    return None
