from functools import partial
from glob import glob
import logging
import multiprocessing
import os
import random
import re
from typing import NamedTuple, Optional, Union, cast

import pandas as pd
from rich.progress import track

from ..core import ParseError, parse
from ..science_log import ScienceLog, science_log


class ResultRow(NamedTuple):
    run: int
    clone: int
    gen: int
    os: str
    platform_name: str
    platform_vendor: str
    platform_version: str
    device_name: str
    device_vendor: str
    device_version: str
    device_driver_version: str
    cuda_enabled: bool
    perf_ns_per_day: Optional[float]


def get_log_file_path(
    project_data_path: str,
    run: Union[int, str],
    clone: Union[int, str],
    gen: Union[int, str],
) -> str:
    return os.path.join(
        project_data_path, f"RUN{run}", f"CLONE{clone}", f"results{gen}", "science.log"
    )


def _parse_log(project_data_path: str, path: str) -> Optional[ResultRow]:

    regex = get_log_file_path(
        project_data_path,
        r"(?P<run>[0-9]+)",
        r"(?P<clone>[0-9]+)",
        r"(?P<gen>[0-9])",
    )

    match = re.search(regex, path)

    if match is None:
        logging.warning("Path %s didn't match regex %s", path, regex)
        return None

    try:
        log = cast(ScienceLog, parse(science_log, path))

        if log.core_log.cuda and log.core_log.cuda.enabled:
            try:
                cuda_platform = next(
                    platform
                    for platform in log.core_log.platforms
                    if platform.info.name == "NVIDIA CUDA"
                )
            except StopIteration:
                raise RuntimeError(
                    "Core22 reported CUDA enabled, "
                    "but didn't find CUDA in listed platforms: "
                    + ", ".join(
                        platform.info.name for platform in log.core_log.platforms
                    )
                )
            platform_info, device = (
                cuda_platform.info,
                cuda_platform.devices[log.core_log.cuda.gpu],
            )
        else:
            platform_info, device = log.get_active_device()
    except (ParseError, RuntimeError, UnicodeDecodeError) as e:
        logging.warning("Parse error: %s: %s", path, e)
        return None

    return ResultRow(
        run=int(match["run"]),
        clone=int(match["clone"]),
        gen=int(match["gen"]),
        os=log.core_header.platform,
        platform_name=platform_info.name,
        platform_vendor=platform_info.vendor,
        platform_version=platform_info.version,
        device_name=device.name,
        device_vendor=device.vendor,
        device_version=device.version,
        device_driver_version=device.driver_version,
        cuda_enabled=log.core_log.cuda is not None and log.core_log.cuda.enabled,
        perf_ns_per_day=log.core_log.average_perf_ns_day,
    )


def parse_project_logs(
    project_data_path: str, num_procs: Optional[int] = None, sample: int = None
) -> pd.DataFrame:

    pattern = get_log_file_path(project_data_path, "*", "*", "*")
    parse_log = partial(_parse_log, project_data_path)

    files = glob(pattern)
    if sample is not None:
        files = random.choices(files, k=sample)

    with multiprocessing.Pool(processes=num_procs) as pool:
        iter_results = pool.imap_unordered(parse_log, files)
        results = list(track(iter_results, total=len(files)))

    records = [r._asdict() for r in results if r is not None]
    num_failed = len(files) - len(records)

    if num_failed > 0:
        logging.warning("Failed to parse %d files out of %d", num_failed, len(files))

    return pd.DataFrame.from_records(records).set_index(["run", "clone", "gen"])
