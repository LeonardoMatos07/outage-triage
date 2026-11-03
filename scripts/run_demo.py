import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass

from app.settings import ROOT

API_PORT = 8000
CHAT_PORT = 8501
DASHBOARD_PORT = 8502
STARTUP_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 1


@dataclass(frozen=True)
class Service:
    name: str
    command: list[str]
    health_url: str


def streamlit_command(script: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        script,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]


def services() -> list[Service]:
    return [
        Service(
            "api",
            [sys.executable, "-m", "uvicorn", "app.api:app", "--port", str(API_PORT)],
            f"http://localhost:{API_PORT}/health",
        ),
        Service(
            "chat",
            streamlit_command("ui/chat.py", CHAT_PORT),
            f"http://localhost:{CHAT_PORT}/_stcore/health",
        ),
        Service(
            "dashboard",
            streamlit_command("ui/dashboard.py", DASHBOARD_PORT),
            f"http://localhost:{DASHBOARD_PORT}/_stcore/health",
        ),
    ]


def build_environment(real: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["API_URL"] = f"http://localhost:{API_PORT}"
    if not real:
        environment["LLM_MODE"] = "mock"
    return environment


def is_healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return bool(response.status == 200)
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


def wait_until_healthy(service: Service, process: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        if is_healthy(service.health_url):
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return False


def stop_all(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="scripts.run_demo")
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    environment = build_environment(args.real)
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for service in services():
            process = subprocess.Popen(service.command, cwd=ROOT, env=environment)
            processes.append(process)
            if not wait_until_healthy(service, process):
                print(f"{service.name} did not start")
                return 1
            print(f"{service.name} ready at {service.health_url}")
        chat_url = f"http://localhost:{CHAT_PORT}"
        dashboard_url = f"http://localhost:{DASHBOARD_PORT}"
        print(f"chat: {chat_url}\ndashboard: {dashboard_url}\nCtrl+C to stop")
        if not args.no_browser:
            webbrowser.open(chat_url)
            webbrowser.open(dashboard_url)
        while all(process.poll() is None for process in processes):
            time.sleep(POLL_INTERVAL_SECONDS)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        stop_all(processes)


if __name__ == "__main__":
    sys.exit(main())
