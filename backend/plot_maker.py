import yaml
from pathlib import Path
import pandas as pd
import altair as alt


def read_header(md_file: Path, output_keys: list = None) -> dict:
    """Load yaml header from a markdown file."""
    with open(md_file, "r") as file:
        # Read lines until the second "---"
        lines = []
        yaml_delimiter_count = 0
        for line in file:
            if line.strip() == "---":
                yaml_delimiter_count += 1
                if yaml_delimiter_count > 1:
                    break
            elif yaml_delimiter_count > 0:
                lines.append(line)

        # Join the lines and parse the YAML
        yaml_content = "".join(lines)

    output = yaml.safe_load(yaml_content)
    if output_keys is None:
        return output
    return {k: v for k, v in output.items() if k in output_keys}


def make_plot(post_dir: Path, save: Path | None = None) -> alt.Chart:
    """Make an Altair plot to display publications by year using data from Markdown files.

    To align the plot number with the frontend, we must extract and regenerate data from .md files
    rather than using the data from papers.yaml.
    """

    data = [read_header(file, output_keys=["year"]) for file in post_dir.glob("*.md")]
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
