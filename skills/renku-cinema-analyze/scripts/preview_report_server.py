#!/usr/bin/env python3
"""Serve Renku Cinema Analyze reports on one stable local preview port."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import tempfile
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
BASE_DIR: Path | None = None
PID_FILE = Path(tempfile.gettempdir()) / "renku-cinema-analyze-preview.pid"
LEGACY_PID_FILES = (
    Path(tempfile.gettempdir()) / "renku-visual-language-preview.pid",
    Path(tempfile.gettempdir()) / "filmgrab-visual-language-preview.pid",
)


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


def is_server_healthy(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25) as sock:
            request = f"GET /health HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            sock.sendall(request.encode("ascii"))
            return b'"ok": true' in sock.recv(512)
    except OSError:
        return False


def read_pid() -> int | None:
    for pid_file in (PID_FILE, *LEGACY_PID_FILES):
        try:
            return int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            continue
    return None


def remove_pid_file_for(pid: int) -> None:
    for pid_file in (PID_FILE, *LEGACY_PID_FILES):
        try:
            if int(pid_file.read_text(encoding="utf-8").strip()) == pid:
                pid_file.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            continue


def read_pid_from_current_file() -> int | None:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def remove_pid() -> None:
    try:
        if read_pid_from_current_file() == os.getpid():
            PID_FILE.unlink()
    except FileNotFoundError:
        pass


def daemonize(log_file: Path) -> None:
    """Detach the server so wrapper scripts can return while the preview stays alive."""
    first_pid = os.fork()
    if first_pid > 0:
        os._exit(0)

    os.setsid()

    second_pid = os.fork()
    if second_pid > 0:
        os._exit(0)

    os.chdir("/")
    os.umask(0o022)
    sys.stdin.flush()
    sys.stdout.flush()
    sys.stderr.flush()

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(os.devnull, "rb", buffering=0) as stdin, open(log_file, "ab", buffering=0) as log:
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())


def stop_server() -> int:
    pid = read_pid()
    if not pid:
        print("No preview server pid file found.")
        return 0
    if not is_process_running(pid):
        remove_pid_file_for(pid)
        print(f"Removed stale preview server pid file for pid {pid}.")
        return 0
    os.kill(pid, signal.SIGTERM)
    remove_pid_file_for(pid)
    print(f"Stopped Renku Cinema Analyze preview server pid {pid}.")
    return 0


def status() -> int:
    pid = read_pid()
    if pid and is_process_running(pid) and is_server_healthy():
        print(f"Renku Cinema Analyze preview server appears to be running on pid {pid}.")
        return 0
    if pid:
        remove_pid_file_for(pid)
    print("Renku Cinema Analyze preview server is not running.")
    return 1


def resolve_analysis_path(raw_dir: str | None, raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    if raw_dir:
        return (Path(raw_dir).expanduser().resolve() / "analysis.json")
    raise ValueError("Missing dir or path query parameter.")


def library_root() -> Path:
    if BASE_DIR is None:
        raise ValueError("No base analysis folder is configured for the preview server.")
    return BASE_DIR


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
    if raw_dir or raw_path:
        analysis_path = resolve_analysis_path(raw_dir, raw_path)
        current_dir = analysis_path.parent.resolve()
        parent = current_dir.parent.resolve()
    else:
        current_dir = None
        parent = library_root()

    items = []
    for candidate in sorted(parent.iterdir(), key=lambda item: item.name.lower()):
        if not candidate.is_dir():
            continue
        candidate_analysis = candidate / "analysis.json"
        if not candidate_analysis.is_file():
            continue
        candidate_dir = candidate.resolve()
        items.append(
            {
                "title": film_title_from_analysis(candidate_analysis),
                "dir": str(candidate_dir),
                "current": current_dir is not None and candidate_dir == current_dir,
            }
        )
    items.sort(key=lambda item: item["title"].lower())
    return {
        "currentDir": str(current_dir) if current_dir else None,
        "parentDir": str(parent),
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
                self.send_json(400, {"error": str(exc)})
                return
            self.send_json(200, data)
            return

        if parsed.path == "/health":
            self.send_json(200, {"ok": True, "pid": os.getpid(), "baseDir": str(BASE_DIR) if BASE_DIR else None})
            return

        self.send_json(404, {"error": "Not found"})


def serve(host: str, port: int, base_dir: Path | None) -> int:
    global BASE_DIR
    BASE_DIR = base_dir.resolve() if base_dir else None
    if BASE_DIR and not BASE_DIR.is_dir():
        raise ValueError(f"Base analysis folder does not exist: {BASE_DIR}")

    pid = read_pid()
    if pid and is_process_running(pid) and is_server_healthy(host, port) and pid != os.getpid():
        print(f"Renku Cinema Analyze preview server already appears to be running on pid {pid}.")
        print(f"Use: http://{host}:{port}/?dir=/absolute/path/to/movie-folder")
        return 0
    if pid:
        remove_pid_file_for(pid)

    server = ThreadingHTTPServer((host, port), ReportHandler)
    write_pid()
    print(f"Renku Cinema Analyze preview server running at http://{host}:{port}/")
    if BASE_DIR:
        print(f"Base analysis folder: {BASE_DIR}")
    print(f"Use: http://{host}:{port}/?dir=/absolute/path/to/movie-folder")
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
    parser.add_argument("--base-dir", help="Base folder for the home-page movie picker")
    parser.add_argument("--daemon", action="store_true", help="Detach and keep serving after the wrapper exits")
    parser.add_argument("--log-file", default=str(Path(tempfile.gettempdir()) / "renku-cinema-analyze-preview.log"))
    parser.add_argument("--stop", action="store_true", help="Stop the preview server using its pid file")
    parser.add_argument("--status", action="store_true", help="Report whether the preview server is running")
    args = parser.parse_args()

    if args.stop:
        return stop_server()
    if args.status:
        return status()
    if args.daemon:
        daemonize(Path(args.log_file).expanduser())
        print(f"\n--- Renku Cinema Analyze preview server started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---", flush=True)
    return serve(args.host, args.port, Path(args.base_dir).expanduser() if args.base_dir else None)


if __name__ == "__main__":
    raise SystemExit(main())
