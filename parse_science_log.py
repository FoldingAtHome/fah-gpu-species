from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from parsy import (
    Parser,
    any_char,
    eof,
    generate,
    letter,
    regex,
    seq,
    string,
    whitespace,
)
from typing import Callable, List

decimal_number = regex(r"[0-9]+").map(int)

floating = regex(r"[0-9\.]+").map(float)

newline = string("\n")


def line_with(p: Parser) -> Parser:
    return whitespace.optional() >> p << newline


def many_until(p: Parser, until: Parser, term_desc="") -> Parser:
    return (until.should_fail(term_desc) >> p).many()


@dataclass_json
@dataclass
class SemVer:
    major: int
    minor: int
    patch: int


@dataclass_json
@dataclass
class Arg:
    key: str
    val: str


@dataclass_json
@dataclass
class FahCoreHeader:
    core: str
    type_: str
    version: SemVer
    author: str
    copyright_: str
    homepage: str
    date: datetime
    time: str
    revision: str
    branch: str
    compiler: str
    options: str
    platform: str
    bits: str
    mode: str
    maintainers: str
    args: List[Arg]


@dataclass_json
@dataclass
class PlatformInfo:
    profile: str
    version: str
    name: str
    vendor: str


@dataclass_json
@dataclass
class Device:
    name: str
    vendor: str
    version: str


@dataclass_json
@dataclass
class Platform:
    info: PlatformInfo
    devices: List[Device]


@dataclass_json
@dataclass
class FahCoreLog:
    version: SemVer
    platforms: List[Platform]
    checkpoint_perfs_ns_day: List[float]
    average_perf_ns_day: float


@dataclass_json
@dataclass
class ScienceLog:
    fah_core_header: FahCoreHeader
    fah_core_log: FahCoreLog


semver = decimal_number.sep_by(string(".")).combine(SemVer)

section_break = string("*") * 80 >> newline


def heading(name: Parser) -> Parser:
    return line_with(regex(r"\*+") >> name << regex(r"\*+"))


any_heading = heading(regex(r"[^\*\n]+")).map(str.strip)


def match_heading(sec_name: str) -> Parser:
    return heading(whitespace >> string(sec_name) << whitespace)


def prop(key: Parser, value: Parser):
    @generate
    def inner():
        k = yield key
        yield string(": ")
        v = yield value
        return k, v

    return line_with(inner)


any_prop = prop(letter.at_least(1).concat(), regex(r"[^\n]+"))


def match_prop(name: str, value: Parser) -> Parser:
    return prop(string(name), value).map(lambda p: p[1])


def string_prop(name: str) -> Parser:
    return match_prop(name, many_until(any_char, any_prop | any_heading).concat())


@generate
def arg():
    yield string("-")
    key = yield regex(r"[^\s]+")
    yield whitespace
    val = yield regex(r"[^\s]+")
    return Arg(key, val)


fah_core_header = match_heading("Core22 Folding@home Core") >> seq(
    core=string_prop("Core"),
    type_=string_prop("Type"),
    version=match_prop("Version", semver),
    author=string_prop("Author"),
    copyright_=string_prop("Copyright"),
    homepage=string_prop("Homepage"),
    date=string_prop("Date").map(lambda s: datetime.strptime(s, "%b %d %Y")),
    time=string_prop("Time"),
    revision=string_prop("Revision"),
    branch=string_prop("Branch"),
    compiler=string_prop("Compiler"),
    options=string_prop("Options"),
    platform=string_prop("Platform"),
    bits=string_prop("Bits"),
    mode=string_prop("Mode"),
    maintainers=string_prop("Maintainers"),
    args=match_prop("Args", arg.sep_by(whitespace)),
).combine_dict(FahCoreHeader)


version_decl = string("Version ") >> semver << newline


def var_def(var_name: str):
    return (
        whitespace
        >> string(f"{var_name} =")
        >> whitespace
        >> regex("[^\n]+").concat()
        << newline
    )


def platform_device_section(i: int, parser):
    return whitespace >> string(f"-- {i} --") >> newline >> parser


def numbered_list(get_parser: Callable[[int], Parser], length: int):
    return seq(*[get_parser(i) for i in range(length)])


def platform(platform_idx: int):
    return (
        whitespace
        >> string(f"-- {platform_idx} --")
        >> newline
        >> seq(
            profile=var_def("PROFILE"),
            version=var_def("VERSION"),
            name=var_def("NAME"),
            vendor=var_def("VENDOR"),
        ).combine_dict(PlatformInfo)
    )


platforms_decl = (
    string("[") >> decimal_number << string("] compatible platform(s):") << newline
)


def platform_device(device_idx: int):
    return (
        whitespace
        >> string(f"-- {device_idx} --")
        >> newline
        >> seq(
            name=var_def("DEVICE_NAME"),
            vendor=var_def("DEVICE_VENDOR"),
            version=var_def("DEVICE_VERSION"),
        ).combine_dict(Device)
    )


def platform_devices_decl(platform_idx: int):
    return (
        string("(")
        >> decimal_number
        << string(f") device(s) found on platform {platform_idx}:")
        << newline
    )


def platform_devices(platform_idx: int):
    @generate
    def inner():
        num_devices = yield platform_devices_decl(platform_idx)
        devices = yield numbered_list(platform_device, num_devices)
        yield newline
        return devices

    return inner

perf = floating << string(" ns/day")

perf_checkpoint = line_with(string("Performance since last checkpoint: ") >> perf)

perf_average = line_with(string("Average performance: ") >> perf)


@generate
def fah_core_log():
    yield section_break
    yield string("Folding@home GPU Core22 Folding@home Core")
    yield newline
    version = yield version_decl
    num_platforms = yield platforms_decl
    platforms = yield numbered_list(platform, num_platforms)
    yield newline
    devices = yield numbered_list(platform_devices, num_platforms)
    yield many_until(any_char, perf_checkpoint)
    checkpoint_perfs = yield perf_checkpoint.sep_by(
        many_until(any_char, perf_checkpoint | eof)
    )
    average_perf = yield perf_average

    platforms = [
        Platform(platform, platform_devices)
        for platform, platform_devices in zip(platforms, devices)
    ]

    return FahCoreLog(
        version=version,
        platforms=platforms,
        checkpoint_perfs_ns_day=checkpoint_perfs,
        average_perf_ns_day=average_perf,
    )


@generate
def science_log():
    header = yield fah_core_header
    yield (any_heading >> many_until(any_char, any_heading | section_break)) * 3
    log = yield fah_core_log
    yield any_char.many()
    return ScienceLog(header, log)


def parse(input_file: str):
    with open(input_file, "r") as f:
        text = f.read()

    print(science_log.parse(text).to_json())


if __name__ == "__main__":
    import fire

    fire.Fire(parse)
