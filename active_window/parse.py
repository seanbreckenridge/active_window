import json
import csv
import logging
from io import StringIO
from pathlib import Path
from typing import NamedTuple, Union, Iterator, Optional, Literal
from datetime import datetime, timezone

import more_itertools


class AWParserError(ValueError):
    def __init__(self, msg: str, path: Path) -> None:
        super().__init__(msg)
        self.path = path


ErrorPolicy = Literal["raise", "drop"]


class AWAndroidEvent(NamedTuple):
    """
    data from the activitywatch android app
    """

    timestamp: datetime
    duration: float
    app: str
    classname: str
    package: str


class AWComputerEvent(NamedTuple):
    """
    data from the aw-window-watcher on your computer
    """

    timestamp: datetime
    duration: float
    app: str
    title: str


class AWWindowWatcherEvent(NamedTuple):
    """
    parsed from CSV files
    https://github.com/seanbreckenridge/aw-watcher-window
    """

    timestamp: datetime
    duration: float
    app: str
    title: str


def parse_window_events(
    pth: Path,
    logger: Optional[logging.Logger] = None,
    error_policy: ErrorPolicy = "drop",
) -> Iterator[Union[AWWindowWatcherEvent, AWAndroidEvent, AWComputerEvent]]:
    if pth.suffix == ".csv":
        yield from _parse_csv_events(pth, logger=logger, error_policy=error_policy)
    else:
        yield from _parse_json_events(pth)


def _parse_datetime_sec(d: Union[str, float, int]) -> datetime:
    return datetime.fromtimestamp(int(float(d)), tz=timezone.utc)


def _parse_csv_events(
    pth: Path,
    logger: Optional[logging.Logger],
    error_policy: ErrorPolicy = "drop",
) -> Iterator[AWWindowWatcherEvent]:
    with pth.open("r", encoding="utf-8", newline="") as f:
        contents = f.read()
    # convert line breaks to unix style; i.e. broken ^M characters
    buf = StringIO(contents.replace("\r", ""))
    csv_reader = csv.reader(
        buf, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    row = None
    while True:
        try:
            row = next(csv_reader)
            yield AWWindowWatcherEvent(
                timestamp=_parse_datetime_sec(row[0]),
                duration=float(row[1]),
                app=row[2],
                title=row[3],
            )
        except ValueError as ve:
            if error_policy == "raise":
                raise AWParserError(f"Error parsing {pth} {row} {ve}", pth) from ve
            if logger:
                logger.debug(f'Error parsing "{pth}" {row} {ve}')
        except csv.Error as e:
            # some lines contain the NUL byte for some reason... ??
            # seems to be x-lib/encoding errors causing malformed application/file names
            # catch those and ignore them
            #
            # seems to happen when computer force shuts down/x-server doesnt have a chance
            # to stop properly
            if error_policy == "raise":
                raise AWParserError(f"Error parsing {pth} {row} {e}", pth) from e
            if logger:
                logger.debug(f'Error parsing "{pth}" {row} {e}')
        except StopIteration:
            return


def _parse_datetime(ds: str) -> datetime:
    utc_naive = datetime.fromisoformat(ds.rstrip("Z"))
    return utc_naive.replace(tzinfo=timezone.utc)


def _parse_json_events(pth: Path) -> Iterator[Union[AWAndroidEvent, AWComputerEvent]]:
    data = json.loads(pth.read_text())
    buckets = data["buckets"]
    for val in buckets.values():
        # check if this doesnt match schema
        if "events" not in val:
            continue
        first = more_itertools.first(val["events"], None)
        if first is None:
            continue
        if "data" not in first:
            continue
        appdata = first["data"]
        if "app" not in appdata:
            continue
        data = appdata.keys()
        is_computer = "title" in data
        is_phone = "classname" in data and "package" in data
        if not is_computer and not is_phone:
            continue

        if is_computer:
            for event in val["events"]:
                dat = event["data"]
                yield AWComputerEvent(
                    timestamp=_parse_datetime(event["timestamp"]),
                    duration=event["duration"],
                    app=dat["app"],
                    title=dat["title"],
                )
        else:
            assert is_phone
            for event in val["events"]:
                dat = event["data"]
                yield AWAndroidEvent(
                    timestamp=_parse_datetime(event["timestamp"]),
                    duration=event["duration"],
                    app=dat["app"],
                    package=dat["package"],
                    classname=dat["classname"],
                )
