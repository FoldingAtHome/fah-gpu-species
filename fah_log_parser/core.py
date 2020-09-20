from typing import cast

from parsy import ParseError, Parser
from pydantic import BaseModel


class Model(BaseModel):
    class Config:
        allow_mutation = False
        extra = "forbid"


def parse(parser: Parser, input_file: str) -> Model:
    with open(input_file, "r") as f:
        text = f.read()

    return cast(Model, parser.parse(text))
