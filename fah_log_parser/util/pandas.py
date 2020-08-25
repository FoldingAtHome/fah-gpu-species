from dataclasses import asdict, dataclass
from functools import partial
from glob import glob
import logging
import multiprocessing
import os
import re
from typing import Optional, Union
import pandas as pd
from tqdm.auto import tqdm
from ..core import ParseError, parse
from ..science_log import science_log


@dataclass
class ResultRow:
    run: int
    clone: int
    gen: int
    device_name: str
    perf_ns_per_day: float


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
        project_data_path, r"(?P<run>[0-9]+)", r"(?P<clone>[0-9]+)", r"(?P<gen>[0-9])",
    )

    match = re.search(regex, path)

    if match is None:
        logging.warning("Path %s didn't match regex %s", path, regex)
        return None

    try:
        log = parse(science_log, path)
        device_name = log.get_active_device().name
    except (ParseError, ValueError) as e:
        logging.warning("Parse error: %s: %s", path, e)
        return None

    return ResultRow(
        run=int(match["run"]),
        clone=int(match["clone"]),
        gen=int(match["gen"]),
        device_name=device_name,
        perf_ns_per_day=log.fah_core_log.average_perf_ns_day,
    )


def parse_logs_to_df(
    project_data_path: str, num_procs: Optional[int] = None,
) -> pd.DataFrame:

    pattern = get_log_file_path(project_data_path, "*", "*", "*")
    files = glob(pattern)
    parse_log = partial(_parse_log, project_data_path)

    with multiprocessing.Pool(processes=num_procs) as pool:
        iter_results = pool.imap_unordered(parse_log, files)
        results = list(tqdm(iter_results, total=len(files)))

    records = [asdict(r) for r in results if r is not None]
    num_failed = len(files) - len(records)

    if num_failed > 0:
        logging.warning("Failed to parse %d files out of %d", num_failed, len(files))

    return pd.DataFrame.from_records(records)
