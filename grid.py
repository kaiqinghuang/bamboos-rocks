#!/usr/bin/env python3
"""
bamboos-photos 下应有 112 个子文件夹（000–111），每个文件夹放 9 张 1080×1920 图片。
程序实时播放：16×7 网格，从左上角 (0,0) 开始，每个格子依次展示该文件夹的 9 张图，
每 0.5 秒切换一张；当前格子播完后移动到下一个格子（从左到右、从上到下）。
按 q 或 Esc 退出。
"""

import time
from pathlib import Path

import cv2
from PIL import Image

# 画布尺寸（竖版）
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

# 网格：16 列 × 7 行 = 112 块
COLS = 16
ROWS = 7
TILE_WIDTH = CANVAS_WIDTH // COLS    # 67
TILE_HEIGHT = CANVAS_HEIGHT // ROWS  # 274

PHOTOS_DIR = Path(__file__).parent / "bamboos-photos"

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
FOLDERS_PER_GRID = COLS * ROWS  # 112
IMAGES_PER_FOLDER = 9
INTERVAL = 0.5  # 秒


def load_image(path: Path) -> Image.Image:
    """加载图片，校验为 1080×1920 竖版。"""
    img = Image.open(path).convert("RGB")
    if img.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        raise ValueError(
            f"{path.name}: 期望尺寸 {CANVAS_WIDTH}×{CANVAS_HEIGHT}，实际为 {img.size[0]}×{img.size[1]}"
        )
    return img


def list_images(folder: Path) -> list[Path]:
    """返回文件夹内排序后的图片列表，最多取前 9 张。"""
    images = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in EXTENSIONS and p.is_file()
    )
    if not images:
        raise ValueError(f"文件夹 {folder.name} 中没有图片")
    if len(images) < IMAGES_PER_FOLDER:
        print(f"警告：文件夹 {folder.name} 只有 {len(images)} 张图，将循环播放")
    return images


def main() -> None:
    folders = sorted(
        p for p in PHOTOS_DIR.iterdir()
        if p.is_dir() and p.name.isdigit()
    )

    if len(folders) < FOLDERS_PER_GRID:
        raise ValueError(
            f"需要 {FOLDERS_PER_GRID} 个数字命名的文件夹，实际找到 {len(folders)} 个"
        )

    folders = folders[:FOLDERS_PER_GRID]

    # 预加载每个文件夹的图片列表
    folder_images = [list_images(f) for f in folders]

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0))
    window_name = "Grid Player"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, CANVAS_WIDTH, CANVAS_HEIGHT)

    total_slots = FOLDERS_PER_GRID * IMAGES_PER_FOLDER
    played = 0

    try:
        for index, folder in enumerate(folders):
            col = index % COLS
            row = index // COLS
            x = col * TILE_WIDTH
            y = row * TILE_HEIGHT

            images = folder_images[index]

            for i in range(IMAGES_PER_FOLDER):
                img_path = images[i % len(images)]
                source = load_image(img_path)
                tile = source.crop((x, y, x + TILE_WIDTH, y + TILE_HEIGHT))
                canvas.paste(tile, (x, y))

                # PIL RGB -> OpenCV BGR
                frame = cv2.cvtColor(
                    __import__("numpy").array(canvas), cv2.COLOR_RGB2BGR
                )
                cv2.imshow(window_name, frame)

                played += 1
                remaining = total_slots - played
                print(
                    f"[{played:04d}/{total_slots}] 文件夹 {folder.name} "
                    f"({i + 1}/{IMAGES_PER_FOLDER}) → {img_path.name} "
                    f"| 网格 ({col}, {row}) | 剩余 {remaining} 帧"
                )

                # 等待 INTERVAL，同时响应按键
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
