from parsy import ParseError, Parser


def parse(parser: Parser, input_file: str):
    with open(input_file, "r") as f:
        text = f.read()

    return parser.parse(text)
