from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..exceptions import UnsafeCommandError


class CommandResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.ok = returncode == 0

    def __iter__(self):
        yield self.returncode
        yield self.stdout
        yield self.stderr

    def __getitem__(self, index: int):
        return (self.returncode, self.stdout, self.stderr)[index]


def platform_info() -> dict:
    return {
        "os": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "available_memory_bytes": 0,
        "ikichunk_version": "0.2.0",
    }


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def normalize_path(path: str) -> str:
    return str(Path(path).expanduser())


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        if host in {"localhost", "127.0.0.1", "::1"}:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(timeout)
                    sock.connect((host if host != "::1" else "::1", port))
                    return True
            except (OSError, socket.timeout, KeyboardInterrupt):
                return False

        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (OSError, socket.timeout, KeyboardInterrupt):
        return False

    for _, _, _, _, address in infos:
        try:
            with socket.socket(socket.AF_INET if ":" not in str(address[0]) else socket.AF_INET6, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect(address)
                return True
        except (OSError, socket.timeout, KeyboardInterrupt):
            continue

    return False


def run(command, *, check: bool = False, shell: bool = False, timeout: Optional[float] = None):
    if isinstance(command, str):
        if any(ch in command for ch in ["|", ">", "<", "&&", "||"]):
            raise UnsafeCommandError(
                "Command string contains shell metacharacters: {!r}. Pass a list[str] instead, or split shell operators into separate run() calls.".format(command))
        command = [command]
    if shell and isinstance(command, list) and len(command) == 1:
        command = command[0]
    completed = subprocess.run(
        command, capture_output=True, text=True, shell=shell, timeout=timeout)
    result = CommandResult(completed.returncode,
                           completed.stdout, completed.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result
