# active_window

library to parse:

- JSON export from activitywatch app for your phone
- JSON export from activitywatch app for your computer
- CSV files from my aw-window fork [(window_watcher)](https://github.com/seanbreckenridge/aw-watcher-window)

## Installation

Requires `python3.7+`

To install with pip, run:

```
python3 install git+https://github.com/seanbreckenridge/active_window
```

## Usage

```
Usage: active_window parse [OPTIONS] DUMP

  parse a JSON or CSV (window_watcher) file

Options:
  -j, --json  Print result to STDOUT as JSON
  --help      Show this message and exit.
```

To use from python:

```python
from pathlib import Path
from active_window.parse import parse_window_events

data = list(parse_window_events(Path("./file.json")))
```

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/active_window'
cd ./active_window
pip install '.[testing]'
flake8 ./active_window
mypy ./active_window
```
