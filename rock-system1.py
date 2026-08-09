#!/usr/bin/env python3
"""
单图实时播放器：监听 rock1/，新图落盘立即播出。
- 实测相邻新图的到达间隔（滑动平均），在其中点插播"当前图往前数 10 张"的旧图，
  视觉速率翻倍；间隔估计随 ComfyUI 产出速度自动变化，不写死
- 补播积压时（实测间隔 < MIN_INTERP_INTERVAL）自动关闭插帧，全速追赶进度
- 没有新图时画面定格在最后一张
- 按 f 切换无边框全屏（4K 竖屏上 2160x3840 点对点）；按 q 或 Esc 退出
"""

import time
from pathlib import Path

import cv2
import numpy as np

PHOTOS_DIR = Path(__file__).parent / "rock1"
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# 白色背景画布 2160x3840，播放图 1872x2808 居中
CANVAS_WIDTH = 2160
CANVAS_HEIGHT = 3840
IMAGE_WIDTH = 1872
IMAGE_HEIGHT = 2808
IMAGE_X = (CANVAS_WIDTH - IMAGE_WIDTH) // 2   # 144
IMAGE_Y = (CANVAS_HEIGHT - IMAGE_HEIGHT) // 2  # 516

WINDOW_NAME = "Rock Player"
WINDOW_WIDTH = 648    # 2160 * 0.3
WINDOW_HEIGHT = 1152  # 3840 * 0.3
POLL = 0.05
QUIT_KEYS = (ord("q"), 27)

WHITE_CANVAS = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), 255, np.uint8)


def compose(image: np.ndarray) -> np.ndarray:
    if image.shape[:2] != (IMAGE_HEIGHT, IMAGE_WIDTH):
        image = cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT))
    canvas = WHITE_CANVAS.copy()
    canvas[IMAGE_Y:IMAGE_Y + IMAGE_HEIGHT, IMAGE_X:IMAGE_X + IMAGE_WIDTH] = image
    return canvas

INTERP_LOOKBACK = 10      # 插帧来源：当前图往前数 10 张
INTERP_EMA_ALPHA = 0.3    # 间隔估计的滑动平均系数（越大跟得越快）
MIN_INTERP_INTERVAL = 2.0  # 实测间隔低于该值视为补播期，不插帧


def list_images() -> list[Path]:
    if not PHOTOS_DIR.exists():
        return []
    return sorted(
        p for p in PHOTOS_DIR.iterdir()
        if p.suffix.lower() in EXTENSIONS and p.is_file()
    )


def show(frame: np.ndarray) -> int:
    cv2.imshow(WINDOW_NAME, frame)
    return cv2.waitKey(1) & 0xFF


def main() -> None:
    PHOTOS_DIR.mkdir(exist_ok=True)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, WINDOW_WIDTH, WINDOW_HEIGHT)

    fullscreen = False

    def handle_key(key: int) -> bool:
        """返回 True 表示退出。"""
        nonlocal fullscreen
        if key in QUIT_KEYS:
            return True
        if key == ord("f"):
            fullscreen = not fullscreen
            prop = cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, prop)
        return False

    if handle_key(show(WHITE_CANVAS)):
        return

    shown: list[Path] = []              # 已播出的主图，按文件名顺序
    estimated_interval: float | None = None  # 相邻主图到达间隔的滑动平均
    last_show_time: float | None = None
    pending_interp: list | None = None  # [触发时刻, 插帧图片路径]

    print("开始播放，按 q 或 Esc 退出")

    try:
        while True:
            images = list_images()

            # 播出所有新到达的主图（有积压时连续补播）
            while len(images) > len(shown):
                path = images[len(shown)]
                frame = cv2.imread(str(path))
                if frame is None:
                    print(f"  {path.name} 读取失败，下轮重试")
                    break
                if handle_key(show(compose(frame))):
                    return

                now = time.monotonic()
                if last_show_time is not None:
                    gap = now - last_show_time
                    estimated_interval = (
                        gap if estimated_interval is None
                        else estimated_interval * (1 - INTERP_EMA_ALPHA)
                        + gap * INTERP_EMA_ALPHA
                    )
                last_show_time = now
                shown.append(path)

                # 新主图到达即抢占旧插帧：以最新间隔估计重新排期中点
                pending_interp = None
                idx = len(shown) - 1
                if (
                    idx >= INTERP_LOOKBACK
                    and estimated_interval is not None
                    and estimated_interval >= MIN_INTERP_INTERVAL
                ):
                    pending_interp = [
                        now + estimated_interval / 2,
                        shown[idx - INTERP_LOOKBACK],
                    ]

                gap_text = f"间隔 {estimated_interval:.2f}s" if estimated_interval else "首张"
                print(f"{path.name}  ({gap_text})")

            # 到点且期间没有更新的主图到达，播插帧
            if pending_interp is not None and time.monotonic() >= pending_interp[0]:
                _, interp_path = pending_interp
                pending_interp = None
                frame = cv2.imread(str(interp_path))
                if frame is not None:
                    if handle_key(show(compose(frame))):
                        return
                    print(f"  ~ 插帧 {interp_path.name}")

            if handle_key(cv2.waitKey(1) & 0xFF):
                break
            time.sleep(POLL)
    except KeyboardInterrupt:
        print("\n用户退出")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
