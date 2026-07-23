# y3nda - python experiments and tools

...

## Installation

### Windows (PowerShell)

```powershell
cd path\to\y3nda
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents activation, use the virtual-environment Python directly instead:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe .\example_config.py
```

### Linux

```bash
cd /path/to/y3nda
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

On Debian or Ubuntu, install the `python3-venv` system package first if the `venv` command is unavailable.

## First examples

The first three examples are in the project root. They all read
`y3nda_config.json` by default. Its `subdir` value names the working
directory (currently `project_test`), and its `log` value controls console
logging.

When `"log": true`, each example mirrors its console output to
`<subdir>/log.txt`. Terminal color codes are removed from the log file.

### Windows (PowerShell)

```powershell
.\venv\Scripts\python.exe .\example_config.py
.\venv\Scripts\python.exe .\example_dotenv.py
.\venv\Scripts\python.exe .\example_menu.py
```

### Linux

```bash
./venv/bin/python example_config.py
./venv/bin/python example_dotenv.py
./venv/bin/python example_menu.py
```

### `example_config.py`

Displays the values from `y3nda_config.json`, including the resolved working
directory and the logging state.

```bash
python example_config.py --help
```

### `example_dotenv.py`

Reads and displays `<subdir>/.env` with `python-dotenv`. Pass `--load` to also
load its variables into the current Python process, or use `--env-file PATH`
to select another file.

```bash
python example_dotenv.py --load
python example_dotenv.py --env-file path/to/other.env
```

The example prints values verbatim, so do not use it with secrets where the
console or log file might be visible to other people.

### `example_menu.py`

Provides a small interactive editor for `<subdir>/.env`:

- `L` - load values from `.env`
- `S` - show loaded values
- `A` - add or change one value in memory
- `W` - write values to `.env`
- `E` - exit

The menu uses green for successful actions and yellow/orange for highlighted
shortcuts and warnings. Colors work in current Windows terminals and Linux
terminals; they are disabled automatically for redirected output.

## Notes

...
