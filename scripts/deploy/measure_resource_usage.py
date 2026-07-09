#!/usr/bin/env python3
"""Measure pipeline and dashboard resource usage for deployment sizing.

The script avoids third-party dependencies so it can run on a small cloud VM
before the application stack is fully tuned.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "resource_measurements"
PAGE_SIZE_KB = os.sysconf("SC_PAGE_SIZE") // 1024
CLOCK_TICKS = os.sysconf("SC_CLK_TCK")


def _now_label() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _read_proc_stat(pid: int) -> dict[str, float] | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None

    fields = stat.rsplit(") ", 1)[1].split()
    utime_ticks = int(fields[11])
    stime_ticks = int(fields[12])
    rss_pages = int(fields[21])
    rss_mb = rss_pages * PAGE_SIZE_KB / 1024
    vmrss_mb = rss_mb
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            vmrss_mb = int(line.split()[1]) / 1024
            break

    return {
        "rss_mb": vmrss_mb,
        "cpu_seconds": (utime_ticks + stime_ticks) / CLOCK_TICKS,
    }


def _children_by_parent() -> dict[int, list[int]]:
    children: dict[int, list[int]] = {}
    for proc_dir in Path("/proc").iterdir():
        if not proc_dir.name.isdigit():
            continue
        try:
            status = (proc_dir / "status").read_text(encoding="utf-8")
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        parent_pid: int | None = None
        for line in status.splitlines():
            if line.startswith("PPid:"):
                parent_pid = int(line.split()[1])
                break
        if parent_pid is not None:
            children.setdefault(parent_pid, []).append(int(proc_dir.name))
    return children


def _process_tree(root_pid: int) -> list[int]:
    children = _children_by_parent()
    found: list[int] = []
    stack = [root_pid]
    while stack:
        pid = stack.pop()
        found.append(pid)
        stack.extend(children.get(pid, []))
    return found


def _sample_process_tree(root_pid: int) -> dict[str, float]:
    rss_mb = 0.0
    cpu_seconds = 0.0
    alive_processes = 0
    for pid in _process_tree(root_pid):
        sample = _read_proc_stat(pid)
        if sample is None:
            continue
        alive_processes += 1
        rss_mb += sample["rss_mb"]
        cpu_seconds += sample["cpu_seconds"]
    return {
        "process_rss_mb": rss_mb,
        "process_cpu_seconds": cpu_seconds,
        "process_count": float(alive_processes),
    }


def _parse_memory_to_mb(value: str) -> float | None:
    text = value.strip().replace(" ", "")
    if not text:
        return None
    units = [
        ("gib", 1024.0),
        ("gb", 1000.0),
        ("mib", 1.0),
        ("mb", 1.0),
        ("kib", 1 / 1024.0),
        ("kb", 1 / 1000.0),
        ("b", 1 / (1000.0 * 1000.0)),
    ]
    lowered = text.lower()
    for suffix, multiplier in units:
        if lowered.endswith(suffix):
            try:
                return float(lowered[: -len(suffix)]) * multiplier
            except ValueError:
                return None
    try:
        return float(lowered)
    except ValueError:
        return None


def _container_stats(container_names: list[str]) -> dict[str, float]:
    if not container_names:
        return {"container_mem_mb": 0.0}

    stats: dict[str, float] = {}
    total = 0.0
    for name in container_names:
        command = ["podman", "stats", "--no-stream", "--format", "json", name]
        try:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0 or not completed.stdout.strip():
            continue
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            continue
        rows = payload if isinstance(payload, list) else [payload]
        for row in rows:
            if not isinstance(row, dict):
                continue
            mem_value = (
                row.get("mem_usage")
                or row.get("MemUsage")
                or row.get("mem")
                or row.get("Mem")
                or ""
            )
            mem_text = str(mem_value).split("/", 1)[0]
            mem_mb = _parse_memory_to_mb(mem_text)
            if mem_mb is None:
                continue
            key = f"container_{name}_mem_mb"
            stats[key] = mem_mb
            total += mem_mb
    stats["container_mem_mb"] = total
    return stats


def _terminate_process(process: subprocess.Popen[str], timeout_seconds: float = 10.0) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=timeout_seconds)


def _open_log(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", newline="", encoding="utf-8")


class Sampler:
    def __init__(self, csv_path: Path, containers: list[str], interval_seconds: float) -> None:
        self.csv_path = csv_path
        self.containers = containers
        self.interval_seconds = interval_seconds
        self.rows: list[dict[str, float]] = []

    def sample(self, start_time: float, process: subprocess.Popen[str] | None) -> None:
        row: dict[str, float] = {
            "elapsed_seconds": time.perf_counter() - start_time,
            "process_rss_mb": 0.0,
            "process_cpu_seconds": 0.0,
            "process_count": 0.0,
        }
        if process is not None and process.poll() is None:
            row.update(_sample_process_tree(process.pid))
        row.update(_container_stats(self.containers))
        row["total_rss_mb"] = row["process_rss_mb"] + row.get("container_mem_mb", 0.0)
        self.rows.append(row)

    def sleep_until_next(self) -> None:
        time.sleep(self.interval_seconds)

    def write_csv(self) -> None:
        if not self.rows:
            return
        fieldnames: list[str] = []
        for row in self.rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        with _open_log(self.csv_path) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

    def summary(self) -> dict[str, float]:
        if not self.rows:
            return {}
        cpu_samples = [row.get("process_cpu_seconds", 0.0) for row in self.rows]
        max_cpu = max(cpu_samples)
        elapsed = self.rows[-1]["elapsed_seconds"]
        return {
            "sample_count": float(len(self.rows)),
            "elapsed_seconds": elapsed,
            "peak_process_rss_mb": max(row.get("process_rss_mb", 0.0) for row in self.rows),
            "peak_container_mem_mb": max(row.get("container_mem_mb", 0.0) for row in self.rows),
            "peak_total_rss_mb": max(row.get("total_rss_mb", 0.0) for row in self.rows),
            "process_cpu_seconds": max_cpu,
        }


def _write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pipeline_command(config: str, extra_args: list[str]) -> list[str]:
    if extra_args:
        return extra_args
    return ["uv", "run", "sra-explorer", "--config", config, "run-workflow"]


def measure_pipeline(args: argparse.Namespace) -> int:
    label = args.label or f"pipeline-{_now_label()}"
    output_dir = Path(args.output_dir)
    command = _pipeline_command(args.config, args.command)
    csv_path = output_dir / f"{label}.csv"
    summary_path = output_dir / f"{label}.json"
    stdout_path = output_dir / f"{label}.stdout.log"
    stderr_path = output_dir / f"{label}.stderr.log"

    print(f"Running pipeline command: {shlex.join(command)}", flush=True)
    start = time.perf_counter()
    sampler = Sampler(csv_path, args.containers, args.interval)
    with _open_log(stdout_path) as stdout_file, _open_log(stderr_path) as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            start_new_session=True,
        )
        try:
            while process.poll() is None:
                sampler.sample(start, process)
                sampler.sleep_until_next()
            sampler.sample(start, process)
        except KeyboardInterrupt:
            _terminate_process(process)
            raise
    elapsed = time.perf_counter() - start
    sampler.write_csv()
    summary = sampler.summary()
    summary.update(
        {
            "mode": "pipeline",
            "command": command,
            "returncode": process.returncode,
            "elapsed_seconds": elapsed,
            "csv_path": str(csv_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
    )
    _write_summary(summary_path, summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return int(process.returncode or 0)


def _request(url: str, data: dict[str, Any] | None = None, timeout: float = 30.0) -> bytes:
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(url, data=body, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _wait_for_dashboard(base_url: str, timeout_seconds: float) -> None:
    deadline = time.perf_counter() + timeout_seconds
    last_error: Exception | None = None
    while time.perf_counter() < deadline:
        try:
            _request(base_url, timeout=5.0)
            return
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"Dashboard did not become ready at {base_url}: {last_error}")


def _dash_update_payload(tab: str) -> dict[str, Any]:
    return {
        "output": "..tab-content.children...kpi-row.children..",
        "outputs": [
            {"id": "tab-content", "property": "children"},
            {"id": "kpi-row", "property": "children"},
        ],
        "inputs": [
            {"id": "main-tabs", "property": "value", "value": tab},
            {"id": "sa4-filter", "property": "value", "value": []},
            {"id": "sa2-filter", "property": "value", "value": []},
            {"id": "poi-group-filter", "property": "value", "value": []},
            {"id": "top-n", "property": "value", "value": 10},
        ],
        "state": [],
        "changedPropIds": ["main-tabs.value"],
    }


def _dashboard_command(args: argparse.Namespace) -> list[str]:
    if args.command:
        return args.command
    bind = f"{args.host}:{args.port}"
    return [
        "uv",
        "run",
        "gunicorn",
        "data2001.task4.dashboard_wsgi:server",
        "--bind",
        bind,
        "--workers",
        str(args.workers),
        "--threads",
        str(args.threads),
        "--timeout",
        str(args.timeout),
    ]


def measure_webapp(args: argparse.Namespace) -> int:
    label = args.label or f"webapp-{args.tab}-{_now_label()}"
    output_dir = Path(args.output_dir)
    command = _dashboard_command(args)
    csv_path = output_dir / f"{label}.csv"
    summary_path = output_dir / f"{label}.json"
    stdout_path = output_dir / f"{label}.stdout.log"
    stderr_path = output_dir / f"{label}.stderr.log"
    base_url = f"http://{args.host}:{args.port}"
    update_url = f"{base_url}/_dash-update-component"

    env = os.environ.copy()
    env["DATA2001_CONFIG"] = args.config
    print(f"Starting dashboard command: {shlex.join(command)}", flush=True)
    start = time.perf_counter()
    sampler = Sampler(csv_path, args.containers, args.interval)
    latencies: list[float] = []
    bytes_received = 0
    with _open_log(stdout_path) as stdout_file, _open_log(stderr_path) as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            start_new_session=True,
        )
        try:
            _wait_for_dashboard(base_url, args.startup_timeout)
            for _ in range(args.warmup_requests):
                _request(update_url, _dash_update_payload(args.tab), timeout=args.timeout)
            for _ in range(args.requests):
                request_start = time.perf_counter()
                response = _request(update_url, _dash_update_payload(args.tab), timeout=args.timeout)
                latencies.append(time.perf_counter() - request_start)
                bytes_received += len(response)
                sampler.sample(start, process)
                sampler.sleep_until_next()
            sampler.sample(start, process)
        finally:
            _terminate_process(process)
    elapsed = time.perf_counter() - start
    sampler.write_csv()
    latency_sorted = sorted(latencies)
    p95_latency = latency_sorted[int((len(latency_sorted) - 1) * 0.95)] if latency_sorted else 0.0
    summary = sampler.summary()
    summary.update(
        {
            "mode": "webapp",
            "tab": args.tab,
            "command": command,
            "request_count": len(latencies),
            "elapsed_seconds": elapsed,
            "mean_latency_seconds": sum(latencies) / len(latencies) if latencies else 0.0,
            "p95_latency_seconds": p95_latency,
            "max_latency_seconds": max(latencies) if latencies else 0.0,
            "response_bytes_total": bytes_received,
            "csv_path": str(csv_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
    )
    _write_summary(summary_path, summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--config", default="configs/local.yaml")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument(
        "--containers",
        default="data2001-postgis",
        help="Comma-separated Podman container names to include, or empty string to skip.",
    )
    parser.add_argument("--label", default="")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    pipeline = subparsers.add_parser("pipeline", help="Measure sra-explorer run-workflow.")
    pipeline.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional custom command after --, for example -- uv run sra-explorer check-db.",
    )
    pipeline.set_defaults(func=measure_pipeline)

    webapp = subparsers.add_parser("webapp", help="Measure dashboard startup and Dash callback requests.")
    webapp.add_argument("--host", default="127.0.0.1")
    webapp.add_argument("--port", type=int, default=8050)
    webapp.add_argument("--workers", type=int, default=2)
    webapp.add_argument("--threads", type=int, default=4)
    webapp.add_argument("--timeout", type=int, default=120)
    webapp.add_argument("--startup-timeout", type=float, default=60.0)
    webapp.add_argument("--tab", choices=["overview", "score-map", "poi-map", "income", "tables"], default="income")
    webapp.add_argument("--warmup-requests", type=int, default=2)
    webapp.add_argument("--requests", type=int, default=10)
    webapp.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional custom dashboard command after --.",
    )
    webapp.set_defaults(func=measure_webapp)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.containers = [name.strip() for name in args.containers.split(",") if name.strip()]
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
