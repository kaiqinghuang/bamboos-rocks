#!/usr/bin/env python3
"""
15×10 网格静态拼合脚本。
- PHOTOS_DIR 为一个平铺的大文件夹，内含 150 张 1872×2808 的图
- 150 个格子按从左到右、从上到下依此对应排序后的 150 张图
- 每张图裁剪其对应格子在画布上的区域，拼合成一张 1872×2808 的图输出
- 每个格子左下角标注数字编号，从 1 到最右下角的格子
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1872
CANVAS_HEIGHT = 2808

COLS = 22
ROWS = 14

# 改成实际存放 150 张图的文件夹名
PHOTOS_DIR = Path(__file__).parent / "rock1"
OUTPUT_PATH = Path(__file__).parent / "output" / "grid-rock1.1.png"

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TOTAL_SLOTS = COLS * ROWS

LABEL_COLOR = "#685850"
LABEL_SIZE = 20
LABEL_PADDING = 8


def list_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in EXTENSIONS and p.is_file()
    )


def load_font() -> ImageFont.ImageFont:
    for name in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, LABEL_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    images = list_images(PHOTOS_DIR)
    if not images:
        raise FileNotFoundError(f"没有找到图片: {PHOTOS_DIR}")

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT))
    # 数字标号功能暂时停用
    # draw = ImageDraw.Draw(canvas)
    # font = load_font()

    for slot in range(TOTAL_SLOTS):
        # 格子数超过图片数时取模循环，从头重新取用
        img_path = images[slot % len(images)]
        source = Image.open(img_path).convert("RGB")
        if source.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
            source = source.resize((CANVAS_WIDTH, CANVAS_HEIGHT))

        col = slot % COLS
        row = slot // COLS
        # 宽高除以行列数可能除不尽，用整除边界让所有格子铺满画布，不留缝隙
        x0 = col * CANVAS_WIDTH // COLS
        y0 = row * CANVAS_HEIGHT // ROWS
        x1 = (col + 1) * CANVAS_WIDTH // COLS
        y1 = (row + 1) * CANVAS_HEIGHT // ROWS

        canvas.paste(source.crop((x0, y0, x1, y1)), (x0, y0))
        # 数字标号功能暂时停用；anchor="ld" 以文字左下角为定位点，编号从 1 开始
        # draw.text(
        #     (x0 + LABEL_PADDING, y1 - LABEL_PADDING),
        #     str(slot + 1),
        #     font=font,
        #     fill=LABEL_COLOR,
        #     anchor="ld",
        # )
        print(f"{img_path.name} -> 格子({col}, {row})")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT_PATH)
    print(f"\n已输出: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
