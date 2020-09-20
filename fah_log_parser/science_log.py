from datetime import datetime
from typing import Callable, List, NamedTuple, Optional, Tuple

from .core import Model
from parsy import (
    Parser,
    any_char,
    decimal_digit,
    generate,
    letter,
    regex,
    seq,
    string,
    whitespace,
)

some_digits = decimal_digit.at_least(1).concat()

integer = some_digits.map(int).desc("integer")

floating = (
    (some_digits + string(".") + some_digits).map(float).desc("floating-point number")
)

newline = string("\n")

dash = string("-")


def line_with(p: Parser) -> Parser:
    return whitespace.optional() >> p << newline


def except_(p: Parser, e: Parser, description: str) -> Parser:
    return e.should_fail(f"not {description}") >> p


def many_until(p: Parser, until: Parser, description: str) -> Parser:
    return except_(p, until, description).many()


def many_until_string(p: Parser, s: str) -> Parser:
    return many_until(p, string(s), s)


def bracketed(p: Parser) -> Parser:
    return string("[") >> p << string("]")


def parenthesized(p: Parser) -> Parser:
    return string("(") >> p << string(")")


class SemVer(Model):
    major: int
    minor: int
    patch: int


class CommandArg(Model):
    key: str
    val: Optional[str]


class FahCoreHeader(Model):
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
    args: List[CommandArg]


class PlatformInfo(Model):
    profile: str
    version: str
    name: str
    vendor: str


class Device(Model):
    name: str
    vendor: str
    version: str


class Platform(Model):
    info: PlatformInfo
    devices: List[Device]


class FahCoreLog(Model):
    version: SemVer
    platforms: List[Platform]
    checkpoint_perfs_ns_day: List[float]
    average_perf_ns_day: Optional[float]


def arg_value(key: str, args: List[CommandArg]) -> Optional[str]:
    try:
        return next(arg for arg in args if arg.key == key).val
    except StopIteration:
        return None


class ScienceLog(Model):
    fah_core_header: FahCoreHeader
    fah_core_log: FahCoreLog

    def get_active_device(self) -> Tuple[PlatformInfo, Device]:
        opencl_platform = arg_value("opencl-platform", self.fah_core_header.args)
        opencl_device = arg_value("opencl-device", self.fah_core_header.args)

        platform_idx = 0 if opencl_platform is None else int(opencl_platform)
        device_idx = 0 if opencl_device is None else int(opencl_device)

        try:
            platform = self.fah_core_log.platforms[platform_idx]
            return platform.info, platform.devices[device_idx]
        except IndexError:
            raise ValueError(
                f"Didn't find a match for the OpenCL platform, device: "
                f"{platform_idx}, {device_idx}"
            )


def heading(name: Parser) -> Parser:
    return line_with(
        string("*").at_least(1)
        >> whitespace
        >> name
        << whitespace
        << string("*").at_least(1)
    ).desc("heading")


any_heading = heading(many_until_string(any_char, " *"))


def match_heading(name: str) -> Parser:
    return heading(string(name))


def prop(key: Parser, value: Parser) -> Parser:
    @generate
    def inner():
        k = yield key
        yield string(": ")
        v = yield value
        return k, v

    return line_with(inner)


def match_prop(name: str, value: Parser) -> Parser:
    return prop(string(name), value).map(lambda p: p[1])


any_char_except_newline = except_(any_char, newline, "newline")


any_prop_firstline = prop(
    letter.at_least(1).concat(), any_char_except_newline.at_least(1).concat()
)


def string_prop(name: str) -> Parser:
    return match_prop(
        name,
        many_until(
            any_char, any_prop_firstline | any_heading, "property or heading"
        ).concat(),
    )


@generate
def command_arg():
    yield dash
    key = (
        yield except_(any_char, whitespace, "whitespace")
        .at_least(1)
        .concat()
        .desc("argument key")
    )
    val = yield (
        whitespace
        >> except_(any_char, whitespace | dash, "whitespace or dash")
        .at_least(1)
        .concat()
        .desc("argument value")
    ).optional()
    return CommandArg(key=key, val=val)


semver = seq(
    major=integer << string("."), minor=integer << string("."), patch=integer
).combine_dict(SemVer)

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
    args=match_prop("Args", command_arg.sep_by(whitespace)),
).combine_dict(FahCoreHeader)


def var_def(var_name: str) -> Parser:
    return line_with(
        string(f"{var_name} =")
        >> whitespace
        >> any_char_except_newline.at_least(1).concat()
    )


def platform(platform_idx: int) -> Parser:
    return line_with(string(f"-- {platform_idx} --")) >> seq(
        profile=var_def("PROFILE"),
        version=var_def("VERSION"),
        name=var_def("NAME"),
        vendor=var_def("VENDOR"),
    ).combine_dict(PlatformInfo)


def platform_device(device_idx: int) -> Parser:
    return line_with(string(f"-- {device_idx} --")) >> seq(
        name=var_def("DEVICE_NAME"),
        vendor=var_def("DEVICE_VENDOR"),
        version=var_def("DEVICE_VERSION"),
    ).combine_dict(Device)


def platform_devices_decl(platform_idx: int) -> Parser:
    return line_with(
        parenthesized(integer)
        << string(f" device(s) found on platform {platform_idx}:")
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
    version_decl = line_with(string("Version ") >> semver)
    platforms_decl = line_with(bracketed(integer) << string(" compatible platform(s):"))
    perf = floating << string(" ns/day")
    perf_checkpoint = line_with(string("Performance since last checkpoint: ") >> perf)
    perf_average = line_with(string("Average performance: ") >> perf)

    yield line_with(string("Folding@home GPU Core22 Folding@home Core"))
    version = yield version_decl
    num_platforms = yield platforms_decl
    platforms = yield numbered_list(platform, num_platforms)
    yield newline
    devices = yield numbered_list(platform_devices, num_platforms)
    yield many_until(any_char, perf_checkpoint, "checkpoint")
    checkpoint_perfs = yield perf_checkpoint.sep_by(
        many_until(
            any_char,
            perf_checkpoint | perf_average,
            "checkpoint or average performace",
        )
    )
    average_perf = yield perf_average.optional()

    return FahCoreLog(
        version=version,
        platforms=[
            Platform(info=platform, devices=platform_devices)
            for platform, platform_devices in zip(platforms, devices)
        ],
        checkpoint_perfs_ns_day=checkpoint_perfs,
        average_perf_ns_day=average_perf,
    )


section_break = line_with(string("*" * 80))

any_section = any_heading >> many_until(
    any_char, any_heading | section_break, "heading or section break"
)


@generate
def science_log() -> Parser:
    header = yield fah_core_header
    yield any_section * 3
    yield section_break
    log = yield fah_core_log
    yield any_char.many()
    return ScienceLog(fah_core_header=header, fah_core_log=log)
