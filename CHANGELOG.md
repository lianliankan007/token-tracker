# Changelog

All notable changes to this project will be documented in this file.

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

