#!/usr/bin/env python3
"""
轮询拉取云端 ComfyUI 输出目录到本地 rock2/，保持远端文件名。
- 下载先写 .tmp 再原子改名，播放器永远读不到写了一半的文件
- 启动时以本地已有文件为基准，不重复下载
- SSH 连接复用（ControlMaster），降低轮询握手开销
启动：python3 sync_remote2.py
"""

import re
import subprocess
import time
from pathlib import Path

REMOTE_HOST = "l4funr0touq0eofh.ssh.x-gpu.com"
REMOTE_PORT = "44794"
REMOTE_USER = "root"
REMOTE_PASS = "o4iK9tM4b7ADpUnxwA1vlfVlubP5bbwW"
REMOTE_DIR = "/root/ComfyUI/output/8.7/rock2"

LOCAL_DIR = Path(__file__).parent / "rock2"
POLL_INTERVAL = 1.0
EXT_RE = re.compile(r"\.(png|jpg|jpeg|webp)$", re.I)

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ControlMaster=auto",
    "-o", "ControlPath=/tmp/rock-sync-rock2-%r@%h:%p",
    "-o", "ControlPersist=60",
]


def run_ssh(cmd: str) -> str:
    full_cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "ssh", "-p", REMOTE_PORT, *SSH_OPTS,
        f"{REMOTE_USER}@{REMOTE_HOST}",
        cmd,
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout


def list_remote_images() -> list[str]:
    output = run_ssh(f"ls -1 {REMOTE_DIR} 2>/dev/null || true")
    return sorted(f.strip() for f in output.splitlines() if EXT_RE.search(f.strip()))


def pull_file(remote_name: str) -> bool:
    final_path = LOCAL_DIR / remote_name
    tmp_path = final_path.with_name(final_path.name + ".tmp")
    remote_path = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}/{remote_name}"

    cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "scp", "-P", REMOTE_PORT, *SSH_OPTS,
        remote_path,
        str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[scp error] {remote_name}: {result.stderr.strip()}")
        tmp_path.unlink(missing_ok=True)
        return False

    tmp_path.rename(final_path)
    return True


def main() -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    done = {p.name for p in LOCAL_DIR.iterdir() if EXT_RE.search(p.name)}
    if done:
        print(f"本地已有 {len(done)} 张，跳过重复下载")

    print(f"监控远程: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}")
    print(f"本地存储: {LOCAL_DIR}")
    print("按 Ctrl+C 退出\n")

    try:
        while True:
            new_names = [n for n in list_remote_images() if n not in done]
            for name in new_names:
                print(f"[pull] {name}")
                if pull_file(name):
                    done.add(name)
                else:
                    print(f"[retry later] {name}")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n退出同步")


if __name__ == "__main__":
    main()
