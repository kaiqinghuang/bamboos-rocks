#!/usr/bin/env python3
"""
接收云端 ComfyUI 生成的图片，按每 9 张自动分文件夹存入 bamboos-photos/000–111/
POST 参数：
  - file: 图片文件（request_field_name 对应 file）
启动：python3 receiver.py
监听：0.0.0.0:5000/upload
"""

from pathlib import Path

from flask import Flask, request

BASE_DIR = Path(__file__).parent / "bamboos-photos"
IMAGES_PER_FOLDER = 9
app = Flask(__name__)

# 记录当前批次状态
current_folder_index = 0
current_folder_count = 0


def get_next_save_path() -> Path:
    global current_folder_index, current_folder_count

    folder_name = f"{current_folder_index:03d}"
    save_dir = BASE_DIR / folder_name
    save_dir.mkdir(parents=True, exist_ok=True)

    current_folder_count += 1
    save_path = save_dir / f"{current_folder_count:02d}.png"

    if current_folder_count >= IMAGES_PER_FOLDER:
        current_folder_index += 1
        current_folder_count = 0

    return save_path


@app.route("/upload", methods=["POST"])
def upload() -> dict:
    if "file" not in request.files:
        return {"error": "missing file"}, 400

    file = request.files["file"]
    save_path = get_next_save_path()
    file.save(save_path)

    print(f"[recv] {save_path.parent.name}/{save_path.name}")
    return {"ok": True, "path": str(save_path)}


@app.route("/reset", methods=["POST"])
def reset() -> dict:
    """重置计数器，从 000 重新开始。"""
    global current_folder_index, current_folder_count
    current_folder_index = 0
    current_folder_count = 0
    return {"ok": True, "message": "reset to 000"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, threaded=True)
