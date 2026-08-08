#!/usr/bin/env python3
"""
16×7 网格无限循环播放系统。
- 从 bamboos-photos/000–999+ 动态读取图片
- 某格无图时原地等待，直到凑齐 9 张
- 112 格播完后回到 000，继续用最新文件夹循环
- 按 q 或 Esc 退出
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
RAW_IMAGE_PATH = Path(__file__).parent / "image/raw.jpg"

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TOTAL_SLOTS = COLS * ROWS
IMAGES_PER_FOLDER = 9
INTERVAL = 0.5
WAIT_POLL = 0.5


def load_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if img.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        img = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
    return img


def is_image_valid(path: Path) -> bool:
    """检查图片是否能正常打开（非半成品）。"""
    try:
        with Image.open(path) as img:
            img.load()
        return True
    except (OSError, SyntaxError):
        return False


def list_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in EXTENSIONS and p.is_file()
    )


def wait_for_valid_image(folder: Path, used: set[Path]) -> Path:
    """等待文件夹中出现下一张完整可用的新图。"""
    while True:
        images = list_images(folder)
        for img in images:
            if img in used:
                continue
            if is_image_valid(img):
                return img
            print(f"  等待 {img.name} 写入完整...")
            time.sleep(1.0)
        time.sleep(WAIT_POLL)


def main() -> None:
    if not RAW_IMAGE_PATH.exists():
        raise FileNotFoundError(f"底图不存在: {RAW_IMAGE_PATH}")

    canvas = Image.open(RAW_IMAGE_PATH).convert("RGB")
    if canvas.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        canvas = canvas.resize((CANVAS_WIDTH, CANVAS_HEIGHT))

    window_name = "Grid Player"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, CANVAS_WIDTH, CANVAS_HEIGHT)

    print("开始无限循环播放，按 q 或 Esc 退出")

    cycle = 0  # 当前循环轮次

    try:
        while True:
            print(f"\n===== 第 {cycle + 1} 轮播放 =====")

            for slot in range(TOTAL_SLOTS):
                # 计算当前格子应该读哪个文件夹
                # 第一轮读 000–111，第二轮读 112–223，依此类推
                folder_index = cycle * TOTAL_SLOTS + slot
                folder_name = f"{folder_index:03d}"
                folder = PHOTOS_DIR / folder_name

                # 严格等待目标文件夹，一张一张播，跳过半成品
                used_images: set[Path] = set()

                for _ in range(IMAGES_PER_FOLDER):
                    img_path = wait_for_valid_image(folder, used_images)
                    used_images.add(img_path)

                    col = slot % COLS
                    row = slot // COLS
                    x = col * TILE_WIDTH
                    y = row * TILE_HEIGHT

                    source = load_image(img_path)
                    tile = source.crop((x, y, x + TILE_WIDTH, y + TILE_HEIGHT))
                    canvas.paste(tile, (x, y))

                    frame = cv2.cvtColor(
                        __import__("numpy").array(canvas), cv2.COLOR_RGB2BGR
                    )
                    cv2.imshow(window_name, frame)

                    print(f"[{folder.name}] {img_path.name}")

                    start = time.time()
                    while time.time() - start < INTERVAL:
                        key = cv2.waitKey(1) & 0xFF
                        if key in (ord("q"), 27):
                            raise KeyboardInterrupt
                        time.sleep(0.005)

            cycle += 1

    except KeyboardInterrupt:
        print("\n用户退出")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
