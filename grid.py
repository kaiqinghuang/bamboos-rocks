#!/usr/bin/env python3
"""
16×7 网格实时播放系统。从 bamboos-photos/000–111 动态读取图片，
某格凑齐 9 张后才开始播放该格；每 0.5 秒切一张。按 q 或 Esc 退出。
"""

import time
from pathlib import Path

import cv2
from PIL import Image

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

COLS = 16
ROWS = 7
TILE_WIDTH = CANVAS_WIDTH // COLS
TILE_HEIGHT = CANVAS_HEIGHT // ROWS

PHOTOS_DIR = Path(__file__).parent / "bamboos-photos"
RAW_IMAGE_PATH = Path(__file__).parent / "raw.jpg"

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TOTAL_SLOTS = COLS * ROWS
IMAGES_PER_FOLDER = 9
INTERVAL = 0.5
WAIT_TIMEOUT = 300  # 等待图片超时（秒）


def load_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if img.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        img = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
    return img


def list_images(folder: Path) -> list[Path]:
    images = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in EXTENSIONS and p.is_file()
    )
    return images


def wait_for_images(folder: Path, timeout: int = WAIT_TIMEOUT) -> list[Path]:
    """轮询等待文件夹凑齐 9 张图。"""
    start = time.time()
    while time.time() - start < timeout:
        images = list_images(folder)
        if len(images) >= IMAGES_PER_FOLDER:
            return images[:IMAGES_PER_FOLDER]
        time.sleep(0.2)
    raise TimeoutError(f"{folder.name}: 等待 {timeout}s 后只有 {len(images)} 张图")


def main() -> None:
    if not RAW_IMAGE_PATH.exists():
        raise FileNotFoundError(f"底图不存在: {RAW_IMAGE_PATH}")

    canvas = Image.open(RAW_IMAGE_PATH).convert("RGB")
    if canvas.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        canvas = canvas.resize((CANVAS_WIDTH, CANVAS_HEIGHT))

    window_name = "Grid Player"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, CANVAS_WIDTH, CANVAS_HEIGHT)

    played = 0
    total_frames = TOTAL_SLOTS * IMAGES_PER_FOLDER

    try:
        for index in range(TOTAL_SLOTS):
            folder_name = f"{index:03d}"
            folder = PHOTOS_DIR / folder_name
            folder.mkdir(parents=True, exist_ok=True)

            print(f"[{index + 1:03d}/{TOTAL_SLOTS}] 等待 {folder_name} 凑齐 {IMAGES_PER_FOLDER} 张图...")
            images = wait_for_images(folder)

            col = index % COLS
            row = index // COLS
            x = col * TILE_WIDTH
            y = row * TILE_HEIGHT

            for i, img_path in enumerate(images):
                source = load_image(img_path)
                tile = source.crop((x, y, x + TILE_WIDTH, y + TILE_HEIGHT))
                canvas.paste(tile, (x, y))

                frame = cv2.cvtColor(
                    __import__("numpy").array(canvas), cv2.COLOR_RGB2BGR
                )
                cv2.imshow(window_name, frame)

                played += 1
                print(f"  [{played:04d}/{total_frames}] {img_path.name}")

                start = time.time()
                while time.time() - start < INTERVAL:
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27):
                        raise KeyboardInterrupt
                    time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n用户退出")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
