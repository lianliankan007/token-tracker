import json
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import webview


@dataclass
class DailyUsage:
    total: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_output_tokens: int = 0
    token_events: int = 0


@dataclass
class OverallUsage:
    total: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_output_tokens: int = 0
    files_scanned: int = 0


class LocalSQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracked_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scanned_at TEXT NOT NULL,
                    files_scanned INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cached_input_tokens INTEGER NOT NULL,
                    reasoning_output_tokens INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_usage (
                    run_id INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cached_input_tokens INTEGER NOT NULL,
                    reasoning_output_tokens INTEGER NOT NULL,
                    token_events INTEGER NOT NULL,
                    PRIMARY KEY (run_id, day),
                    FOREIGN KEY (run_id) REFERENCES scan_runs(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    def load_paths(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT path FROM tracked_paths ORDER BY id").fetchall()
        return [str(row["path"]) for row in rows]

    def save_paths(self, paths: List[str]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM tracked_paths")
            conn.executemany("INSERT INTO tracked_paths(path) VALUES(?)", ((p,) for p in paths))
            conn.commit()

    def save_scan_result(self, daily: Dict[str, DailyUsage], totals: OverallUsage) -> None:
        scanned_at = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scan_runs(
                    scanned_at,
                    files_scanned,
                    total,
                    input_tokens,
                    output_tokens,
                    cached_input_tokens,
                    reasoning_output_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scanned_at,
                    totals.files_scanned,
                    totals.total,
                    totals.input_tokens,
                    totals.output_tokens,
                    totals.cached_input_tokens,
                    totals.reasoning_output_tokens,
                ),
            )
            run_id = int(cur.lastrowid)
            conn.executemany(
                """
                INSERT INTO daily_usage(
                    run_id,
                    day,
                    total,
                    input_tokens,
                    output_tokens,
                    cached_input_tokens,
                    reasoning_output_tokens,
                    token_events
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        run_id,
                        day,
                        item.total,
                        item.input_tokens,
                        item.output_tokens,
                        item.cached_input_tokens,
                        item.reasoning_output_tokens,
                        item.token_events,
                    )
                    for day, item in daily.items()
                ),
            )
            conn.commit()

    def load_latest_scan(self) -> Tuple[Optional[Dict[str, DailyUsage]], Optional[OverallUsage]]:
        with self._connect() as conn:
            run = conn.execute(
                """
                SELECT
                    id,
                    files_scanned,
                    total,
                    input_tokens,
                    output_tokens,
                    cached_input_tokens,
                    reasoning_output_tokens
                FROM scan_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if run is None:
                return None, None
            rows = conn.execute(
                """
                SELECT
                    day,
                    total,
                    input_tokens,
                    output_tokens,
                    cached_input_tokens,
                    reasoning_output_tokens,
                    token_events
                FROM daily_usage
                WHERE run_id = ?
                ORDER BY day
                """,
                (run["id"],),
            ).fetchall()

        daily: Dict[str, DailyUsage] = {}
        for row in rows:
            daily[str(row["day"])] = DailyUsage(
                total=int(row["total"]),
                input_tokens=int(row["input_tokens"]),
                output_tokens=int(row["output_tokens"]),
                cached_input_tokens=int(row["cached_input_tokens"]),
                reasoning_output_tokens=int(row["reasoning_output_tokens"]),
                token_events=int(row["token_events"]),
            )

        totals = OverallUsage(
            total=int(run["total"]),
            input_tokens=int(run["input_tokens"]),
            output_tokens=int(run["output_tokens"]),
            cached_input_tokens=int(run["cached_input_tokens"]),
            reasoning_output_tokens=int(run["reasoning_output_tokens"]),
            files_scanned=int(run["files_scanned"]),
        )
        return daily, totals


class TokenParser:
    def __init__(self) -> None:
        self._usage_by_session: Dict[str, Dict[str, int]] = {}
        self._seen_event_fingerprints: set[str] = set()

    @staticmethod
    def _to_num(value: object) -> int:
        if isinstance(value, (int, float)):
            return int(value)
        return 0

    @classmethod
    def _extract_usage(cls, obj: dict) -> dict:
        if not isinstance(obj, dict):
            return {"input": 0, "output": 0, "cached_input": 0, "reasoning_output": 0}

        def pick(*keys: str) -> int:
            for k in keys:
                if k in obj:
                    return cls._to_num(obj.get(k))
            return 0

        return {
            "input": pick("input_tokens", "input_token", "input"),
            "output": pick("output_tokens", "output_token", "output"),
            "cached_input": pick("cached_input_tokens", "cached_input"),
            "reasoning_output": pick("reasoning_output_tokens", "reasoning_output"),
        }

    @staticmethod
    def _event_fingerprint(record: dict, line: str) -> str:
        session_id = str(record.get("session_id") or "")
        timestamp = str(record.get("timestamp") or record.get("created_at") or "")
        event_type = str(record.get("type") or "")
        payload = record.get("payload")
        payload_type = str(payload.get("type") or "") if isinstance(payload, dict) else ""
        info = payload.get("info") if isinstance(payload, dict) else None
        info = info if isinstance(info, dict) else {}
        msg_id = str(record.get("id") or info.get("id") or "")
        if session_id or timestamp or msg_id:
            return "|".join((session_id, timestamp, event_type, payload_type, msg_id))
        return line

    @staticmethod
    def _as_record(obj: dict) -> dict:
        event_msg = obj.get("event_msg")
        if isinstance(event_msg, dict):
            return event_msg
        return obj

    def _calc_increment(self, session_key: str, usage_total: dict, usage_last: dict) -> dict:
        last_total = self._usage_by_session.get(
            session_key,
            {
                "input": 0,
                "output": 0,
                "cached_input": 0,
                "reasoning_output": 0,
            },
        )

        has_total = any(usage_total.values())
        has_last = any(usage_last.values())

        if has_total:
            increment = {
                "input": max(0, usage_total["input"] - last_total["input"]),
                "output": max(0, usage_total["output"] - last_total["output"]),
                "cached_input": max(0, usage_total["cached_input"] - last_total["cached_input"]),
                "reasoning_output": max(0, usage_total["reasoning_output"] - last_total["reasoning_output"]),
            }
            if has_last and not any(increment.values()):
                increment = {
                    "input": usage_last["input"],
                    "output": usage_last["output"],
                    "cached_input": usage_last["cached_input"],
                    "reasoning_output": usage_last["reasoning_output"],
                }
            self._usage_by_session[session_key] = usage_total
            return increment

        if has_last:
            return {
                "input": usage_last["input"],
                "output": usage_last["output"],
                "cached_input": usage_last["cached_input"],
                "reasoning_output": usage_last["reasoning_output"],
            }

        return {
            "input": 0,
            "output": 0,
            "cached_input": 0,
            "reasoning_output": 0,
        }

    @staticmethod
    def _discover_jsonl_files(input_paths: List[str]) -> List[Path]:
        seen: set[str] = set()
        found: List[Path] = []
        for raw in input_paths:
            p = Path(raw)
            if p.is_file() and p.suffix.lower() == ".jsonl":
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(p)
                continue
            if p.is_dir():
                for file in p.rglob("*.jsonl"):
                    key = str(file.resolve())
                    if key not in seen:
                        seen.add(key)
                        found.append(file)
        return found

    @staticmethod
    def _pick_day(obj: dict, file_path: Path) -> str:
        for key in ("timestamp", "created_at", "time"):
            raw = obj.get(key)
            if isinstance(raw, str) and len(raw) >= 10:
                return raw[:10]
        return datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")

    def parse_paths(self, input_paths: List[str]) -> Tuple[Dict[str, DailyUsage], OverallUsage]:
        daily: Dict[str, DailyUsage] = {}
        totals = OverallUsage()

        files = self._discover_jsonl_files(input_paths)
        totals.files_scanned = len(files)

        for file_path in files:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue

                    if not isinstance(obj, dict):
                        continue

                    record = self._as_record(obj)
                    payload = record.get("payload")
                    payload = payload if isinstance(payload, dict) else {}
                    info = payload.get("info")
                    info = info if isinstance(info, dict) else {}

                    usage_total = {"input": 0, "output": 0, "cached_input": 0, "reasoning_output": 0}
                    usage_last = {"input": 0, "output": 0, "cached_input": 0, "reasoning_output": 0}

                    payload_type = str(payload.get("type") or "")
                    event_type = str(record.get("type") or "")
                    is_token_event = payload_type == "token_count" or "token" in event_type or "response" in event_type

                    total_usage_obj = info.get("total_token_usage")
                    if isinstance(total_usage_obj, dict):
                        usage_total = self._extract_usage(total_usage_obj)
                    else:
                        usage_total = self._extract_usage(record.get("usage") if isinstance(record.get("usage"), dict) else {})

                    last_usage_obj = info.get("last_token_usage")
                    if isinstance(last_usage_obj, dict):
                        usage_last = self._extract_usage(last_usage_obj)
                    else:
                        last_response = record.get("last_response")
                        if isinstance(last_response, dict):
                            usage_last = self._extract_usage(
                                last_response.get("usage") if isinstance(last_response.get("usage"), dict) else {}
                            )

                    if not is_token_event and not any(usage_total.values()) and not any(usage_last.values()):
                        continue

                    fingerprint = self._event_fingerprint(record, line)
                    if fingerprint in self._seen_event_fingerprints:
                        continue
                    self._seen_event_fingerprints.add(fingerprint)

                    session_key = str(record.get("session_id") or file_path)
                    inc = self._calc_increment(session_key, usage_total, usage_last)
                    if not any(inc.values()):
                        continue

                    day = self._pick_day(record, file_path)
                    item = daily.setdefault(day, DailyUsage())

                    item.input_tokens += inc["input"]
                    item.output_tokens += inc["output"]
                    item.cached_input_tokens += inc["cached_input"]
                    item.reasoning_output_tokens += inc["reasoning_output"]
                    item.total += inc["input"] + inc["output"]
                    item.token_events += 1

                    totals.input_tokens += inc["input"]
                    totals.output_tokens += inc["output"]
                    totals.cached_input_tokens += inc["cached_input"]
                    totals.reasoning_output_tokens += inc["reasoning_output"]
                    totals.total += inc["input"] + inc["output"]

        return daily, totals


class WebApi:
    def __init__(self) -> None:
        self.config_dir = self._resolve_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.db_file = self.config_dir / "tracker.db"
        self.store = LocalSQLiteStore(self.db_file)
        self.paths = self._load_paths()
        self.window: Optional[webview.Window] = None

    def set_window(self, window: webview.Window) -> None:
        self.window = window

    @staticmethod
    def _fmt_num(num: int) -> str:
        return f"{num:,}"

    @staticmethod
    def _resolve_config_dir() -> Path:
        if sys.platform == "win32":
            appdata_root = Path(os.getenv("APPDATA", str(Path.home())))
        elif sys.platform == "darwin":
            appdata_root = Path.home() / "Library" / "Application Support"
        else:
            appdata_root = Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
        new_dir = appdata_root / "token-tracker"
        legacy_dir = appdata_root / "CodexTokenTracker"

        if not new_dir.exists() and legacy_dir.exists():
            new_dir.mkdir(parents=True, exist_ok=True)
            for name in ("config.json", "tracker.db"):
                src = legacy_dir / name
                dst = new_dir / name
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)
        return new_dir

    @staticmethod
    def _path_identity(path_str: str) -> Tuple[str, bool]:
        path_obj = Path(path_str).expanduser()
        try:
            normalized = str(path_obj.resolve())
        except OSError:
            normalized = str(path_obj.absolute())
        return normalized, path_obj.is_dir()

    def _dedupe_sources(self, paths: List[str]) -> List[str]:
        deduped: List[str] = []
        normalized_paths: List[Path] = []
        normalized_is_dir: List[bool] = []

        for raw in paths:
            normalized, is_dir = self._path_identity(raw)
            current_path = Path(normalized)

            skip = False
            to_remove: List[int] = []
            for idx, (exist_path, exist_is_dir) in enumerate(zip(normalized_paths, normalized_is_dir)):
                if current_path == exist_path:
                    skip = True
                    break
                if is_dir and exist_is_dir:
                    if exist_path in current_path.parents:
                        skip = True
                        break
                    if current_path in exist_path.parents:
                        to_remove.append(idx)
                elif is_dir and (not exist_is_dir):
                    if current_path in exist_path.parents:
                        to_remove.append(idx)
                elif (not is_dir) and exist_is_dir and (exist_path in current_path.parents):
                    skip = True
                    break

            if skip:
                continue

            for idx in reversed(to_remove):
                del deduped[idx]
                del normalized_paths[idx]
                del normalized_is_dir[idx]

            deduped.append(normalized)
            normalized_paths.append(current_path)
            normalized_is_dir.append(is_dir)

        return deduped

    def _load_paths(self) -> List[str]:
        db_paths = self.store.load_paths()
        if db_paths:
            return self._dedupe_sources(db_paths)

        if not self.config_file.exists():
            return []

        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("paths"), list):
                loaded = [str(p) for p in data["paths"] if isinstance(p, str)]
                merged = self._dedupe_sources(loaded)
                self.store.save_paths(merged)
                return merged
        except Exception:
            return []

        return []

    def _save_paths(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.store.save_paths(self.paths)
        payload = {"paths": self.paths}
        self.config_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _rows_payload(rows: List[Tuple[str, DailyUsage]]) -> List[dict]:
        out: List[dict] = []
        for day, item in rows:
            d = asdict(item)
            d["day"] = day
            out.append(d)
        return out

    def _build_payload(
        self,
        daily: Optional[Dict[str, DailyUsage]],
        totals: Optional[OverallUsage],
        status: str,
    ) -> dict:
        rows = sorted((daily or {}).items(), key=lambda x: x[0])
        totals_obj = totals or OverallUsage()
        return {
            "status": status,
            "paths": self.paths,
            "totals": {
                "total": totals_obj.total,
                "input_tokens": totals_obj.input_tokens,
                "output_tokens": totals_obj.output_tokens,
                "cached_input_tokens": totals_obj.cached_input_tokens,
                "reasoning_output_tokens": totals_obj.reasoning_output_tokens,
                "files_scanned": totals_obj.files_scanned,
                "total_fmt": self._fmt_num(totals_obj.total),
                "input_fmt": self._fmt_num(totals_obj.input_tokens),
                "output_fmt": self._fmt_num(totals_obj.output_tokens),
                "files_fmt": self._fmt_num(totals_obj.files_scanned),
            },
            "rows": self._rows_payload(rows),
        }
    def initialize(self) -> dict:
        daily, totals = self.store.load_latest_scan()
        if daily is None or totals is None:
            return self._build_payload({}, OverallUsage(), "等待刷新")
        return self._build_payload(daily, totals, "已加载本地缓存统计")

    def add_directory(self) -> dict:
        if self.window is None:
            return {"ok": False, "message": "窗口未就绪"}
        picked = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if not picked:
            return {"ok": True, "paths": self.paths}
        merged = self._dedupe_sources([*self.paths, *[str(p) for p in picked]])
        if merged != self.paths:
            self.paths = merged
            self._save_paths()
        return {"ok": True, "paths": self.paths}

    def add_files(self) -> dict:
        if self.window is None:
            return {"ok": False, "message": "窗口未就绪"}
        picked = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("JSONL (*.jsonl)", "All files (*.*)"),
        )
        if not picked:
            return {"ok": True, "paths": self.paths}
        merged = self._dedupe_sources([*self.paths, *[str(p) for p in picked]])
        if merged != self.paths:
            self.paths = merged
            self._save_paths()
        return {"ok": True, "paths": self.paths}

    def remove_paths(self, paths_to_remove: List[str]) -> dict:
        remove_set = set(paths_to_remove)
        self.paths = [p for p in self.paths if p not in remove_set]
        self._save_paths()
        return {"ok": True, "paths": self.paths}

    def clear_paths(self) -> dict:
        self.paths = []
        self._save_paths()
        return {"ok": True, "paths": self.paths}

    def refresh_data(self) -> dict:
        if not self.paths:
            return self._build_payload({}, OverallUsage(), "请先添加日志路径")
        try:
            parser = TokenParser()
            daily, totals = parser.parse_paths(self.paths)
            self.store.save_scan_result(daily, totals)
            rows = len(daily)
            status = f"完成：{rows} 天，扫描 {totals.files_scanned} 个文件"
            return self._build_payload(daily, totals, status)
        except Exception as exc:
            return {"error": str(exc)}


def _resource_path(relative: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / relative
    return Path(__file__).parent / relative


def main() -> None:
    api = WebApi()
    index_path = _resource_path("web/index.html")
    window = webview.create_window(
        "token-tracker",
        url=index_path.as_uri(),
        js_api=api,
        width=1280,
        height=820,
        min_size=(1000, 680),
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()

