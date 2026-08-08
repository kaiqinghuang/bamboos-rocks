#!/usr/bin/env python3
"""
单张 SCP 拉取云端 ComfyUI 输出目录，按每 9 张自动分文件夹到 bamboos-photos/000–999+/
依赖：sshpass
启动：python3 sync_remote.py
"""

import re
import subprocess
import time
from pathlib import Path

REMOTE_HOST = "l4funr0touq0eofh.ssh.x-gpu.com"
REMOTE_PORT = "44794"
REMOTE_USER = "root"
REMOTE_PASS = "o4iK9tM4b7ADpUnxwA1vlfVlubP5bbwW"
REMOTE_DIR = "/root/ComfyUI/output/8.7/bamboo2"

LOCAL_BASE = Path(__file__).parent / "bamboos-photos"
IMAGES_PER_FOLDER = 9
POLL_INTERVAL = 1

processed_files: set[str] = set()


def run_ssh(cmd: str) -> str:
    full_cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "ssh", "-p", REMOTE_PORT,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"{REMOTE_USER}@{REMOTE_HOST}",
        cmd,
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout


def list_remote_images() -> list[str]:
    output = run_ssh(f"ls -1 {REMOTE_DIR} 2>/dev/null || true")
    files = [
        f.strip() for f in output.splitlines()
        if re.search(r"\.(png|jpg|jpeg|webp)$", f.strip(), re.I)
    ]
    return sorted(files)


def pull_file(remote_name: str, local_path: Path) -> bool:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    remote_path = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}/{remote_name}"

    cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "scp", "-P", REMOTE_PORT,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        remote_path,
        str(local_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[scp error] {remote_name}: {result.stderr.strip()}")
    return result.returncode == 0


def get_next_save_path() -> Path:
    """找到下一个该写入的本地路径。"""
    folder_index = 0
    while True:
        folder = LOCAL_BASE / f"{folder_index:03d}"
        folder.mkdir(parents=True, exist_ok=True)
        count = len(list(folder.glob("*")))
        if count < IMAGES_PER_FOLDER:
            return folder / f"{count + 1:02d}.png"
        folder_index += 1


def main() -> None:
    LOCAL_BASE.mkdir(parents=True, exist_ok=True)

    print(f"监控远程: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}")
    print(f"本地存储: {LOCAL_BASE}")
    print("按 Ctrl+C 退出\n")

    try:
        while True:
            remote_files = list_remote_images()
            new_files = [f for f in remote_files if f not in processed_files]

            for name in new_files:
                local_path = get_next_save_path()
                print(f"[pull] {name} -> {local_path.parent.name}/{local_path.name}")

                if pull_file(name, local_path):
                    processed_files.add(name)
                else:
                    print(f"[retry later] {name}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n退出同步")


if __name__ == "__main__":
    main()
