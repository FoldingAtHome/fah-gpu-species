from .science_log import science_log
from functools import partial
from parsy import ParseError, Parser


def parse(parser: Parser, input_file: str):
    with open(input_file, "r") as f:
        text = f.read()

    return parser.parse(text)


def _parse_science_log_json(input_file):
    """
    Parse a core22 science.log file and print json to stdout
    """
    return parse(science_log, input_file).to_json()


def cli():
    import fire

    fire.Fire(_parse_science_log_json)
