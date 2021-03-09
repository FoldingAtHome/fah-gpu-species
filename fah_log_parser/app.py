from functools import partial
import logging
import os
from typing import Optional

from parsy import ParseError, Parser
from .core import parse
from .science_log import science_log
from .util.pandas import parse_project_logs


def _parse_log_json(input_file: str) -> str:
    """
    Parse a core22 science.log file and return json.

    Parameters
    ----------
    input_file : str
        Path to science.log file

    Returns
    -------
    str
        JSON-encoded structured data parsed from log file
    """
    return parse(science_log, input_file).json()


def _parse_logs_dataframe(
    *projects: str,
    data_dir: str,
    output: str,
    sample: Optional[int] = None,
    num_procs: Optional[int] = None
) -> None:
    """
    Parse core22 science.log files and write a feather-serialized
    summary dataframe to `output`.
    """
    import pandas as pd
    from rich.progress import track

    print(f'data_dir: {data_dir}')
    print(f'projects: {projects}')
    
    if not projects:        
        logging.warning("no projects specified")
        return

    df = pd.concat(
        {
            project: parse_project_logs(
                os.path.join(data_dir, project),
                sample=sample,
                num_procs=num_procs,
            )
            for project in track(projects)
        },
        names=["project"],
    ).reset_index()

    df.to_feather(output)


def main() -> None:
    import fire

    fire.Fire({"json": _parse_log_json, "dataframe": _parse_logs_dataframe})
