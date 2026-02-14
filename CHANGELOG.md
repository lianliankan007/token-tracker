# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-02-14

### Added

- macOS run script: `run_mac.sh`.
- macOS build script: `build_macos.sh`.
- Platform-specific dependency for macOS (`pyobjc-framework-Cocoa`).
- Cross-platform app-data path docs in README (Windows/macOS/Linux).

### Changed

- Runtime app-data directory resolution is now platform-aware:
  - Windows: `%APPDATA%\\token-tracker\\`
  - macOS: `~/Library/Application Support/token-tracker/`
  - Linux: `~/.local/share/token-tracker/` (or `$XDG_DATA_HOME`)
- README/README.zh-CN now include macOS quick run/build instructions.

## [0.1.0] - 2026-02-14

### Added

- Initial public release of `token-tracker`.
- Desktop app with HTML UI powered by `pywebview`.
- Daily token aggregation and local SQLite persistence.
- Multi-line chart (`Total/Input/Output`) with hover tooltip.
- Codex log parsing support (`token_count` and fallback fields).
- Bilingual documentation (`README.md`, `README.zh-CN.md`).
- MIT license.

### Changed

- Project/app/package naming unified to `token-tracker`.
- App data directory moved to `%APPDATA%\\token-tracker\\`.

### Compatibility

- Automatic migration from legacy `%APPDATA%\\CodexTokenTracker\\` (config/db).

