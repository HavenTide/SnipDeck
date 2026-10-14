# SnipDeck ✨

> 轻量强大的 Windows 截屏录屏工具 — 截图标注、贴图钉屏、高清录屏、OCR 文字识别，开箱即用，快捷键驱动。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

---

## 📸 功能特性

### 截图
- 🎯 **区域截图**：拖拽选区，带放大镜 + 像素级坐标提示
- 🖥️ **全屏截图**：一键整屏，自动进剪贴板
- 🪟 **窗口截图**：自动识别活动窗口
- ✏️ **即时标注**：矩形、椭圆、箭头、画笔、文字、马赛克、橡皮擦
- 📌 **贴图功能**：截图钉在屏幕最顶层，可缩放、可右键另存
- 🔍 **OCR 识别**：截图一键提取文字，自动复制到剪贴板

### 录屏
- ⏺ **区域/全屏录屏**：H.264 硬件加速编码，CPU 占用低
- 🎚️ **帧率可选**：15 / 24 / 30 / 60 fps
- 💾 **MP4 输出**：兼容所有播放器
- 🎛️ **浮动控制条**：录制时可拖拽移动，实时计时

### 效率
- ⌨️ **全局快捷键**：完全自定义，后台随时唤起
- 🕘 **历史记录**：最近 100 条截图录屏随时回看
- 💾 **自动保存 / 自动复制**：按你习惯来
- 🚀 **开机自启**：托盘常驻，不打扰

---

## ⌨️ 默认快捷键

| 功能 | 快捷键 |
|---|---|
| 区域截图 | `Ctrl + Shift + A` |
| 全屏截图 | `Ctrl + Shift + B` |
| 开始 / 停止录屏 | `Ctrl + Shift + R` |
| 贴图（剪贴板转钉图） | `Ctrl + Shift + T` |
| OCR 文字识别 | `Ctrl + Shift + O` |
| 退出截图 | `Esc` |
| 撤销标注 | `Ctrl + Z` |

> 所有快捷键都可以在「设置」里改成你顺手的。

---

## 🚀 快速开始

### 方式一：下载打包好的 exe（推荐）

去 [Releases](../../releases) 页面下载最新版 `SnipDeck.exe`，双击即用，无需安装。

### 方式二：从源码运行

```bash
# 克隆
git clone https://github.com/jumao6868/SnipDeck.git
cd SnipDeck

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

> 首次运行 OCR 功能会自动下载识别模型（约 100MB），请耐心等待。

---

## 📁 项目结构

```
SnipDeck/
├── main.py                 # 入口
├── app/
│   ├── config.py           # 配置管理（自动存到 %APPDATA%）
│   ├── history.py          # 历史记录
│   ├── hotkey.py           # 全局快捷键
│   ├── tray.py             # 系统托盘
│   ├── capture/
│   │   ├── snipper.py      # 选区遮罩 + 标注
│   │   ├── annotate_toolbar.py
│   │   └── pin.py          # 贴图
│   ├── recorder/
│   │   ├── recorder.py     # mss + FFmpeg 录屏核心
│   │   └── record_overlay.py
│   └── ui/
│       ├── settings.py     # 设置窗口
│       └── history_panel.py
├── assets/
└── requirements.txt
```

---

## 🛠️ 技术栈

- **GUI**：PyQt6
- **截屏**：[mss](https://python-mss.readthedocs.io/) — 比 pyautogui 快 3-5 倍
- **录屏**：mss 采集 + FFmpeg（libx264）管道编码
- **快捷键**：keyboard
- **OCR**：EasyOCR
- **打包**：PyInstaller

---

## 🗺️ Roadmap

- [x] 区域截图 + 标注工具栏
- [x] 贴图钉屏
- [x] 录屏（H.264 MP4）
- [x] OCR 文字识别
- [x] 全局快捷键 + 系统托盘
- [x] 历史记录面板
- [ ] 麦克风 + 系统声音同时录制
- [ ] 录屏转 GIF 动图
- [ ] 滚动长截图
- [ ] 录制时高亮鼠标点击
- [ ] 自定义标注颜色主题

---

## 📄 License

MIT License — 随便用，随便改，给个 Star 就好 ⭐

---

**Enjoy SnipDeck!** 如果你觉得好用，欢迎点个 Star，或者提 Issue / PR。
