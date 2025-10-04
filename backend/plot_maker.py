import logging
import re
from pathlib import Path

import altair as alt
import pandas as pd
import yaml


def remove_latex_patterns(x: str) -> str:
    # Define a regular expression pattern for matching LaTeX patterns
    latex_pattern = re.compile(r'\$\S*?\$')
    return re.sub(latex_pattern, '', x)

def read_header(md_file):
    """Load yaml header from a markdown file."""
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the YAML block between --- and ---
    match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
    if not match:
        raise ValueError("No YAML block found")
    
    yaml_block = match.group(1)
    data = yaml.safe_load(yaml_block)
    return data


def make_plot(post_dir: Path, save: Path | None = None) -> alt.Chart:
    """Make an Altair plot to display publications by year using data from Markdown files.

    To align the plot number with the frontend, we must extract and regenerate data from .md files
    rather than using the data from papers.yaml.
    """

    data = []
    for file in post_dir.glob("*.md"):
        try:
            header = read_header(file)
            year = {"year": int(header["year"])}
            data.append(year)

        except Exception as e:
            logging.error(f"Error reading {file}: {e}")
            continue

    df = pd.DataFrame(data).groupby(["year"]).size().rename("count").reset_index()

    plot = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="year:O",
            y=alt.Y("count:Q", title="Number of papers"),
            tooltip=["count:Q"],
        )
        .properties(
            title="Number of Simulation-based Inference Papers by Year",
        )
    )

    if save is not None:
        plot.save(str(save))
    return plot
