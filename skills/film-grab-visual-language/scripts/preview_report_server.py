#!/usr/bin/env python3
"""Serve FilmGrab visual-language reports on one stable local preview port."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PID_FILE = Path(tempfile.gettempdir()) / "filmgrab-visual-language-preview.pid"


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def viewer_html() -> str:
    return (skill_dir() / "assets" / "viewer.html").read_text(encoding="utf-8")


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def remove_pid() -> None:
    try:
        if read_pid() == os.getpid():
            PID_FILE.unlink()
    except FileNotFoundError:
        pass


def stop_server() -> int:
    pid = read_pid()
    if not pid:
        print("No preview server pid file found.")
        return 0
    if not is_process_running(pid):
        PID_FILE.unlink(missing_ok=True)
        print(f"Removed stale preview server pid file for pid {pid}.")
        return 0
    os.kill(pid, signal.SIGTERM)
    PID_FILE.unlink(missing_ok=True)
    print(f"Stopped FilmGrab preview server pid {pid}.")
    return 0


def status() -> int:
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"FilmGrab preview server appears to be running on pid {pid}.")
        return 0
    print("FilmGrab preview server is not running.")
    return 1


def resolve_analysis_path(raw_dir: str | None, raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    if raw_dir:
        return (Path(raw_dir).expanduser().resolve() / "analysis.json")
    raise ValueError("Missing dir or path query parameter.")


def film_title_from_analysis(analysis_path: Path) -> str:
    try:
        data = json.loads(analysis_path.read_text(encoding="utf-8"))
        film = data.get("film", {}) if isinstance(data, dict) else {}
        title = film.get("title")
        year = film.get("year")
        if title and year:
            return f"{title} ({year})"
        if title:
            return str(title)
    except Exception:
        pass
    return analysis_path.parent.name.replace("-", " ").title()


def sibling_analyses(raw_dir: str | None, raw_path: str | None) -> dict:
    analysis_path = resolve_analysis_path(raw_dir, raw_path)
    current_dir = analysis_path.parent
    parent = current_dir.parent
    items = []
    for candidate in sorted(parent.iterdir(), key=lambda item: item.name.lower()):
        if not candidate.is_dir():
            continue
        candidate_analysis = candidate / "analysis.json"
        if not candidate_analysis.is_file():
            continue
        items.append(
            {
                "title": film_title_from_analysis(candidate_analysis),
                "dir": str(candidate.resolve()),
                "current": candidate.resolve() == current_dir.resolve(),
            }
        )
    items.sort(key=lambda item: item["title"].lower())
    return {
        "currentDir": str(current_dir.resolve()),
        "parentDir": str(parent.resolve()),
        "items": items,
    }


class ReportHandler(BaseHTTPRequestHandler):
    server_version = "FilmGrabPreview/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - BaseHTTPRequestHandler API
        print(f"{self.address_string()} - {format % args}", file=sys.stderr)

    def send_text(self, status_code: int, body: str, content_type: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, status_code: int, body: dict) -> None:
        self.send_text(status_code, json.dumps(body, indent=2), "application/json")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in {"/", "/index.html", "/viewer.html"}:
            self.send_text(200, viewer_html(), "text/html")
            return

        if parsed.path == "/analysis.json":
            try:
                analysis_path = resolve_analysis_path(
                    params.get("dir", [None])[0],
                    params.get("path", [None])[0],
                )
                if analysis_path.name != "analysis.json":
                    raise ValueError("The path query parameter must point to an analysis.json file.")
                data = json.loads(analysis_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.send_json(404, {"error": str(exc)})
                return
            self.send_json(200, data)
            return

        if parsed.path == "/analyses":
            try:
                data = sibling_analyses(
                    params.get("dir", [None])[0],
                    params.get("path", [None])[0],
                )
            except Exception as exc:
                self.send_json(404, {"error": str(exc)})
                return
            self.send_json(200, data)
            return

        if parsed.path == "/health":
            self.send_json(200, {"ok": True, "pid": os.getpid()})
            return

        self.send_json(404, {"error": "Not found"})


def serve(host: str, port: int) -> int:
    pid = read_pid()
    if pid and is_process_running(pid) and pid != os.getpid():
        print(f"FilmGrab preview server already appears to be running on pid {pid}.")
        print(f"Use: http://{host}:{port}/?dir=/absolute/path/to/filmgrab-folder")
        return 0

    server = ThreadingHTTPServer((host, port), ReportHandler)
    write_pid()
    print(f"FilmGrab preview server running at http://{host}:{port}/")
    print(f"Use: http://{host}:{port}/?dir=/absolute/path/to/filmgrab-folder")
    try:
        server.serve_forever()
    finally:
        remove_pid()
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--stop", action="store_true", help="Stop the preview server using its pid file")
    parser.add_argument("--status", action="store_true", help="Report whether the preview server is running")
    args = parser.parse_args()

    if args.stop:
        return stop_server()
    if args.status:
        return status()
    return serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
