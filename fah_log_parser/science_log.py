from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from parsy import (
    Parser,
    any_char,
    generate,
    letter,
    regex,
    seq,
    string,
    whitespace,
)
from typing import Callable, List, Optional

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
class KeyValue:
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
    args: List[KeyValue]


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


def arg_value(key: str, args: List[KeyValue]) -> Optional[str]:
    try:
        return next(arg for arg in args if arg.key == key).val
    except StopIteration:
        return None


@dataclass_json
@dataclass
class ScienceLog:
    fah_core_header: FahCoreHeader
    fah_core_log: FahCoreLog

    def get_active_device(self) -> Device:
        opencl_platform = arg_value("opencl-platform", self.fah_core_header.args)
        opencl_device = arg_value("opencl-device", self.fah_core_header.args)

        platform_idx = 0 if opencl_platform is None else int(opencl_platform)
        device_idx = 0 if opencl_device is None else int(opencl_device)

        try:
            return self.fah_core_log.platforms[platform_idx].devices[device_idx]
        except IndexError as e:
            raise ValueError(
                "Didn't find a match for the OpenCL platform/device "
                "specified in arguments, or no valid OpenCL devices found."
            )


def heading(name: Parser) -> Parser:
    return line_with(regex(r"\*+ ") >> name << regex(r" \*+"))


any_heading = heading(many_until(any_char, string(" *")))


def match_heading(sec_name: str) -> Parser:
    return heading(string(sec_name))


def prop(key: Parser, value: Parser) -> Parser:
    @generate
    def inner():
        k = yield key
        yield string(": ")
        v = yield value
        return KeyValue(k, v)

    return line_with(inner)


def match_prop(name: str, value: Parser) -> Parser:
    return prop(string(name), value).map(lambda p: p.val)


any_prop_firstline = prop(letter.at_least(1).concat(), regex(r"[^\n]+"))


def string_prop(name: str) -> Parser:
    return match_prop(
        name, many_until(any_char, any_prop_firstline | any_heading).concat()
    )


@generate
def arg():
    yield string("-")
    key = yield regex(r"[^\s]+")
    yield whitespace
    val = yield regex(r"[^\s]+")
    return KeyValue(key, val)


semver = decimal_number.sep_by(string(".")).combine(SemVer)

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


def var_def(var_name: str) -> Parser:
    return (
        whitespace
        >> string(f"{var_name} =")
        >> whitespace
        >> regex("[^\n]+").concat()
        << newline
    )


def platform(platform_idx: int) -> Parser:
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


def platform_device(device_idx: int) -> Parser:
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


def platform_devices_decl(platform_idx: int) -> Parser:
    return (
        string("(")
        >> decimal_number
        << string(f") device(s) found on platform {platform_idx}:")
        << newline
    )


def numbered_list(get_parser: Callable[[int], Parser], length: int):
    return seq(*[get_parser(i) for i in range(length)])


def platform_devices(platform_idx: int) -> Parser:
    @generate
    def inner():
        num_devices = yield platform_devices_decl(platform_idx)
        devices = yield numbered_list(platform_device, num_devices)
        yield newline
        return devices

    return inner


@generate
def fah_core_log() -> Parser:
    version_decl = string("Version ") >> semver << newline
    platforms_decl = line_with(
        string("[") >> decimal_number << string("] compatible platform(s):")
    )
    perf = floating << string(" ns/day")
    perf_checkpoint = line_with(string("Performance since last checkpoint: ") >> perf)
    perf_average = line_with(string("Average performance: ") >> perf)

    yield string("Folding@home GPU Core22 Folding@home Core")
    yield newline
    version = yield version_decl
    num_platforms = yield platforms_decl
    platforms = yield numbered_list(platform, num_platforms)
    yield newline
    devices = yield numbered_list(platform_devices, num_platforms)
    yield many_until(any_char, perf_checkpoint)
    checkpoint_perfs = yield perf_checkpoint.sep_by(
        many_until(any_char, perf_checkpoint | perf_average)
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


section_break = string("*") * 80 >> newline

any_section = any_heading >> many_until(any_char, any_heading | section_break)


@generate
def science_log() -> Parser:
    header = yield fah_core_header
    yield any_section * 3
    yield section_break
    log = yield fah_core_log
    yield any_char.many()
    return ScienceLog(header, log)
