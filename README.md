# token-tracker

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/lianliankan007/token-tracker?display_name=tag)](https://github.com/lianliankan007/token-tracker/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-0078D6)](https://www.microsoft.com/windows)

Language: English | [简体中文](./README.zh-CN.md)

`token-tracker` is a local/offline token analytics app for AI coding-assistant logs. It parses log files, aggregates daily usage, and visualizes trends in a desktop app.

Current focus is Codex logs. Future releases will support additional tools like Claude Code and Cursor.

## Features

- Multi-path scan: add multiple folders/files
- Daily aggregation: total, input, output
- Local persistence with SQLite (`paths`, `runs`, `daily usage`)
- Multi-line trend chart (toggle total/input/output)
- Hover tooltip on chart points for detailed values
- Windows one-file `exe` packaging
- macOS local run/build support

## Quick Start

### 1. Requirements

- Windows 10/11 or macOS 13+
- Python 3.10+

```bat
python --version
```

### 2. Install

```bat
cd /d C:\path\to\token-tracker
python -m pip install -r requirements.txt
```

### 3. Run

```bat
python token_tracker.py
```

or

```bat
run.bat
```

### 4. Build EXE

```bat
build_exe.bat
```

Output:

```text
dist\token-tracker.exe
```

### 5. macOS Run/Build

Run on macOS:

```bash
bash run_mac.sh
```

Build on macOS:

```bash
bash build_macos.sh
```

Output binary:

```text
dist/token-tracker
```

## Usage

1. Add log paths (`Add Folder` / `Add File`).
2. Click `Refresh` to parse and aggregate.
3. Use chart toggles (`Total / Input / Output`).
4. Hover over chart points to see per-day details.

### Codex Log Path Tutorial

If you want to analyze Codex usage, you can add either a folder or specific `.jsonl` files:

1. Open `token-tracker`.
2. Click `Add Folder` if you want recursive scan under a directory.
3. Or click `Add File` and select one/more Codex `.jsonl` log files.
4. Confirm the selected paths appear in the left path list.
5. Click `Refresh`.

Suggested approach:

- Prefer `Add Folder` if Codex logs are generated continuously.
- Use `Add File` when you only want to analyze a fixed set of logs.

Typical Windows locations you can check:

```text
%USERPROFILE%\.codex\
%APPDATA%\Codex\
```

If your environment uses a custom log directory, add that directory directly.

### Other Tools (Preview)

`token-tracker` will support Claude Code and Cursor in future versions.
Before official adapters land, users can still help by locating logs and sharing examples.

#### Claude Code log discovery

Try:

1. Search recent `.jsonl` files:
   `Get-ChildItem $env:USERPROFILE -Recurse -Filter *.jsonl -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 50 FullName,LastWriteTime`
2. Run Claude Code once, then repeat the command and compare newly changed files.
3. Add candidate folders/files in `token-tracker` and test refresh.

#### Cursor log discovery

Try:

1. Search under common app data locations:
   `%APPDATA%`, `%LOCALAPPDATA%`, `%USERPROFILE%`
2. Focus on folders containing `cursor`, `logs`, `jsonl`, or session traces.
3. Re-run search after a Cursor coding session and compare recently modified files.

If you confirm stable paths/fields, please open an Issue so we can add first-class adapters.

## Log Parsing (Current)

Primary supported structures:

- `event_msg`
- `payload.type == token_count`
- `payload.info.total_token_usage`
- `payload.info.last_token_usage`

Fallback fields:

- `usage`
- `last_response.usage`

## Data Storage

Default directory by platform:

```text
Windows: %APPDATA%\token-tracker\
macOS:   ~/Library/Application Support/token-tracker/
Linux:   ~/.local/share/token-tracker/ (or $XDG_DATA_HOME/token-tracker/)
```

Files:

- `config.json`: tracked paths
- `tracker.db`: local SQLite data

## Roadmap

- Support additional log sources
- Claude Code adapter
- Cursor adapter
- Unified multi-tool dashboard and comparison
- Finer dimensions (session/project/model)

## Open Source Notes

- Releases are published at: `https://github.com/lianliankan007/token-tracker/releases`
- License: `MIT`

## Contributing

Issues and PRs are welcome.

