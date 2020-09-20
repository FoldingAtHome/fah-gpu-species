from .core import parse
from .science_log import science_log
from functools import partial
from parsy import ParseError, Parser


def _parse_science_log_json(input_file: str) -> str:
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


def main() -> None:
    import fire

    fire.Fire(_parse_science_log_json)
