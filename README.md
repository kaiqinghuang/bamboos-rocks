# bamboos-rocks

云端 ComfyUI 实时出图 → SSH 拉取到本地 → 本地播放器即时上屏的展示系统。
共 4 条独立管线（rock1–rock4），每条 = 一个同步脚本 + 一个播放器 + 一个图片目录，可同时运行互不干扰。

## 管线一览

| 管线  | 图片尺寸     | 白色背景画布   | 方向 | 同步脚本          | 播放器             | 本地目录 |
|-------|--------------|----------------|------|-------------------|--------------------|----------|
| rock1 | 1872 × 2808  | 2160 × 3840    | 竖   | `sync_remote1.py` | `rock-system1.py`  | `rock1/` |
| rock2 | 1872 × 2424  | 2160 × 3840    | 竖   | `sync_remote2.py` | `rock-system2.py`  | `rock2/` |
| rock3 | 1872 × 2736  | 2160 × 3840    | 竖   | `sync_remote3.py` | `rock-system3.py`  | `rock3/` |
| rock4 | 2504 × 1872  | 3840 × 2160    | 横   | `sync_remote4.py` | `rock-system4.py`  | `rock4/` |

图片居中贴在白色画布上，画布尺寸即 4K 分辨率（竖 2160×3840 / 横 3840×2160），在对应方向的 4K 显示器上按 `f` 全屏可点对点显示。

## 依赖

- Python 3 + `opencv-python` + `numpy`（播放器）
- `sshpass`（同步脚本；macOS: `brew tap hudochenkov/sshpass && brew install hudochenkov/sshpass/sshpass`）
- 早期网格脚本额外需要 `Pillow`

## 使用

每条管线开两个终端：

```bash
python3 sync_remote1.py    # 终端 1：持续从云端拉取新图到 rock1/
python3 rock-system1.py    # 终端 2：监听 rock1/，来一张播一张
```

播放器按键：`f` 切换无边框全屏（先拖到目标显示器再按），`q` / `Esc` 退出。

## 播放机制

- **来图即播**：播放器每 0.05s 扫一次目录，无固定播放间隔，跟随 ComfyUI 产出速度
- **自适应中点插帧**：实测相邻新图到达间隔（滑动平均），在间隔中点插播"当前图往前数 10 张"的旧图，视觉速率翻倍；产出快慢变化时自动跟随
- **补播模式**：启动时有积压会按解码速度全速补播（实测间隔 < 2s 时插帧自动关闭），追上后进入实时
- **原子写入**：同步脚本先下载成 `.tmp` 再改名，播放器永远读不到半成品
- **断点续传**：同步脚本启动时以本地已有文件为基准，不重复下载

## 更换云实例（host/端口/密码变了）

改 `sync_remote1~4.py` 顶部的 `REMOTE_HOST` / `REMOTE_PORT` / `REMOTE_PASS`（用到哪条改哪条，四个文件各自独立）。

注意：新实例的 ComfyUI 输出文件名会从 `comfyui_00001_.png` 重新编号，与本地已有文件同名会被跳过导致新旧错位——**换实例时清空对应的本地 `rockN/` 目录**。

## 其他文件

- `rock_wockflow.json`：ComfyUI 工作流导出
- `bamboo-grid-system.py` / `bamboo-grid-static.py`：早期 bamboo 系列的 16×7 网格播放实验（读 `bamboos-photos/`）
- `image/`：底图等素材；`output/`：网格合成输出
