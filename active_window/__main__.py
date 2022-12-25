from typing import Any
from pathlib import Path
from datetime import datetime

import simplejson

import click


def _default(data: Any) -> Any:
    if isinstance(data, datetime):
        return data.timestamp()
    raise TypeError(f"Dont know how to serialize {data}")


def serialize(data: Any) -> str:
    return simplejson.dumps(data, namedtuple_as_object=True, default=_default)


@click.group()
def main() -> None:
    """
    Parses the JSON dump from activitywatchs' window watcher
    """
    pass


@main.command(short_help="parse aw-window dump")
@click.option(
    "-j",
    "--json",
    "_json",
    is_flag=True,
    default=False,
    required=False,
    help="Print result to STDOUT as JSON",
)
@click.argument(
    "DUMP",
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
def parse(_json: bool, dump: Path) -> None:
    """
    parse a JSON or CSV (window_watcher) file
    """
    from .parse import parse_window_events

    data = list(parse_window_events(dump))
    if _json:
        click.echo(serialize(data))
    else:
        from pprint import pprint

        for d in data:
            pprint(d)


if __name__ == "__main__":
    main(prog_name="active_window")
