# token-tracker

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/YOUR_GITHUB_USERNAME/token-tracker?display_name=tag)](https://github.com/YOUR_GITHUB_USERNAME/token-tracker/releases)
[![License](https://img.shields.io/badge/License-Unspecified-lightgrey)](./LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

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

## Quick Start

### 1. Requirements

- Windows 10/11
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

## Usage

1. Add log paths (`Add Folder` / `Add File`).
2. Click `Refresh` to parse and aggregate.
3. Use chart toggles (`Total / Input / Output`).
4. Hover over chart points to see per-day details.

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

Default directory:

```text
%APPDATA%\token-tracker\
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

- Replace badge repo path `YOUR_GITHUB_USERNAME/token-tracker` with your real repo after publishing.
- Add a `LICENSE` file to make the license badge actionable.

## Contributing

Issues and PRs are welcome.

