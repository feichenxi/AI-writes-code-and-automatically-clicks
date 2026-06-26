<div align="center">

# 🤖 AI writes code and automatically clicks

### AI 驱动的代码监督与自动化点击工具集

*让 Windows 那些"运行 / 仍要运行 / 继续 / 确定"弹窗从此自己消失。*

[![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)](https://github.com/feichenxi/AI-writes-code-and-automatically-clicks)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![PyAutoGUI](https://img.shields.io/badge/pyautogui-0.9.54-orange.svg)](https://pyautogui.readthedocs.io/)

</div>

---

## 📖 项目简介 / Overview

**AI writes code and automatically clicks** 是一套面向 Windows 的桌面自动化工具集，核心能力是 **"盯着屏幕 → 识别按钮 → 自动点击 → 自动关闭错误弹窗"**。

它解决一个非常具体的痛点：当你长时间挂机运行某个程序（编译、批处理、爬虫、游戏脚本……）时，系统或应用会时不时弹出 `Microsoft Visual C++ Runtime Library`、`程序已停止工作`、`是否继续运行` 等对话框，**一旦没人点掉，整条流水线就卡住了**。本工具用两种互补方案把这个问题彻底自动化掉：

| 模式 | 思路 | 是否需要管理员 | 是否常驻 | 持久性 |
|------|------|:-------------:|:--------:|:------:|
| 🛡️ **注册表系统级抑制** | 从源头禁用 Windows 错误报告 | ✅ 需要 | ❌ 一次性 | 永久 |
| ⚡ **常驻进程窗口级抑制** | 实时枚举窗口并自动点击确认按钮 | ❌ 不需要 | ✅ 需运行 | 进程退出即失效 |
| 🎯 **图像识别自动点击** | 用 `pyautogui` 在屏幕上找按钮图并点击 | ❌ 不需要 | ✅ 需运行 | 进程退出即失效 |

> 💡 **推荐组合**：先跑一次注册表模式做底层抑制，再常驻运行图像识别模式处理漏网之鱼，双重保险。

---

## ✨ 功能特性 / Features

- 🎯 **图像识别点击** — 自动发现 `ocr/` 目录下的所有按钮截图，扫描全屏匹配后随机点击其中一个（`default.py`）
- 🛡️ **系统级错误抑制** — 一键写入注册表，禁用 Windows Error Reporting、AeDebug 自动调试器，并把 `MSVCR*.dll` / `VCRUNTIME140.dll` 等常见运行库加入 `ExcludedApplications`（`报错点击.py`）
- ⚡ **实时窗口监控** — 通过 `EnumWindows` + `FindWindowExW` + `SendMessage(BM_CLICK)` 自动关闭 VC++ Runtime 错误对话框，三层回退方案：按钮文本 → Button 控件 → 发送回车键（`报错点击.py`）
- 📷 **按钮截图工具** — 5 秒倒计时截取按钮区域，输出 `continue_button.png`（`截图工具.py`）
- 🧪 **OCR 文本识别测试** — 验证 `pyautogui.locateOnText` 是否可用（`test_ocr.py`）
- 💥 **错误触发脚本** — VBScript 故意除零 / 访问空对象 / 数组越界，用来测试监控是否生效（`触发错误.vbs`）
- 🔓 **隐藏恢复入口** — 在主菜单输入 `987789` 可一键还原所有注册表改动
- 🎨 **彩色终端 UI** — CJK / Emoji 等宽计算，让 ASCII 边框在中文环境下也对齐
- 📝 **滚动日志** — `RotatingFileHandler` 自动轮转，单文件 1MB 上限

---

## 🗂️ 项目结构 / Project Structure

```
AI-writes-code-and-automatically-clicks/
├── default.py            # ⭐ 主入口：图像识别自动点击器 v4.0（扫描 ocr/ 下所有按钮图）
├── 报错点击.py            # ⭐ Windows 错误完全处理工具 v2.0（注册表 + 窗口监控双模式）
├── 继续点击.py            # "继续" 按钮专用点击器 v3.0（固定 4 张 continue_button*.png）
├── 简单点击.py            # 按坐标直接点击的简易工具
├── 截图工具.py            # 按钮区域截图工具（5 秒倒计时）
├── test_ocr.py           # 测试 pyautogui 的 locateOnText 文本识别
├── 触发错误.vbs           # VBScript 崩溃测试脚本（用来验证监控是否生效）
├── default.spec          # PyInstaller 打包配置
├── ocr/                  # 📷 按钮图片资源（仓库必需，请勿删除）
│   ├── continue_button.png     # "继续" 按钮
│   ├── run_button.png          # "运行" 按钮
│   ├── still_run_button.png    # "仍要运行" 按钮
│   └── yunxing.png             # "运行" 按钮（中文文件名备份）
├── 使用说明.txt           # 中文使用说明（v2.0）
├── requirements.txt      # Python 依赖清单
├── .gitignore            # 忽略 venv/build/dist/*.exe/*.log 等
├── .gitattributes        # 跨平台换行符归一化
├── LICENSE               # MIT
└── README.md             # 本文件
```

> ⚠️ **`ocr/` 目录下的图片是核心资源，不可删除！** 这些 PNG 是 `pyautogui.locateOnScreen()` 用来做模板匹配的"靶图"。删除后图像识别模式将无法工作。

---

## 🚀 快速开始 / Quick Start

### 1. 环境要求

- **OS**：Windows 10 / 11（依赖 `winreg`、`ctypes.windll`、`msvcrt`，无法在 macOS/Linux 运行 `报错点击.py`）
- **Python**：3.8 或更高
- **屏幕**：建议 100% DPI 缩放（高 DPI 下 `locateOnScreen` 可能需要调高 `confidence`）

### 2. 安装

```bash
# 克隆仓库
git clone https://github.com/feichenxi/AI-writes-code-and-automatically-clicks.git
cd AI-writes-code-and-automatically-clicks

# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate   # macOS / Linux（仅图像识别脚本可跨平台运行）

# 安装依赖
pip install -r requirements.txt
```

### 3. 运行

```bash
# 方式 A：图像识别自动点击（主程序，扫描 ocr/ 下所有按钮图）
python default.py

# 方式 B：Windows 错误完全处理工具（注册表 + 窗口监控双模式）
python 报错点击.py        # 需要管理员权限才能用注册表模式

# 方式 C："继续" 按钮专用点击器
python 继续点击.py

# 方式 D：先截取你自己的按钮图
python 截图工具.py        # 把鼠标移到目标按钮上，倒计时 5 秒后自动截图
```

> 💡 **首次使用图像识别**：如果 `ocr/` 里的图在你机器上匹配不到（不同分辨率 / DPI / 主题会导致按钮外观差异），用 `截图工具.py` 重新截一遍图，覆盖 `ocr/` 下对应文件即可。

### 4. 打包为单文件 EXE（可选）

```bash
pip install pyinstaller
pyinstaller default.spec        # 使用仓库自带的 spec
# 或重新生成
pyinstaller --onefile --console default.py
# 产物在 dist/default.exe
```

---

## 🎮 使用详解 / Usage

### 模式 1：图像识别自动点击（`default.py`）

启动后程序会：

1. 扫描 `ocr/` 目录，加载所有 `*.png` 作为靶图
2. 每 1 秒用 `pyautogui.locateOnScreen(confidence=0.8)` 在屏幕上找匹配
3. 命中后随机选一个，移动鼠标 → 点击 → 休眠 2 秒（避免连点）
4. 按 `Ctrl+C` 安全退出

日志写入 `auto_click.log`（1MB 自动轮转）。

### 模式 2：Windows 错误完全处理（`报错点击.py`）

启动后菜单 3 秒内自动选择 `[2]` 监控模式，也可手动输入：

| 输入 | 行为 |
|------|------|
| `1` | **注册表模式**：禁用 WER / AeDebug / 排除常见运行库 / 停止 `WerSvc` 服务。**需要管理员权限，建议重启系统。** |
| `2` | **监控模式**（推荐）：每 1 秒枚举顶层窗口，匹配 `#32770` 标准对话框 + 标题含 `visual / c++ / runtime / library / host` 关键词的窗口，自动点击确认按钮。无需管理员。 |
| `987789` | 🔓 **隐藏恢复**：还原所有注册表改动，重启 `WerSvc` 为手动启动。 |

监控模式的确认按钮点击有 **三层回退**：

1. `FindWindowExW` 按文本找（`确定 / OK / 是 / Yes / 关闭 / Close`）
2. 失败则按 `Button` 类名找第一个按钮控件
3. 仍失败则 `SetForegroundWindow` + 发送 `VK_RETURN` 回车键

### 模式 3：测试错误触发（`触发错误.vbs`）

双击运行 `触发错误.vbs`，它会依次执行：除以零 → 访问不存在的对象 → 数组越界 → `Err.Raise`，用来验证监控模式是否真的能抓到错误窗口。

---

## ⚙️ 配置 / Configuration

主要可调参数集中在各脚本顶部和 `AutoClicker.__init__` / `monitor_and_click`：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `confidence` | `find_image_position()` | `0.8` | 模板匹配置信度，匹配不到可降到 `0.7`，误匹配可升到 `0.9` |
| `interval` | `monitor_and_click()` | `1` 秒 | 无命中时的扫描间隔 |
| 命中后休眠 | `monitor_and_click()` | `2` 秒 | 点击后等待，避免重复点击同一按钮 |
| `pyautogui.FAILSAFE` | 顶部 | `False` | **已禁用** 失效保护（鼠标移到左上角不会停止） |
| 日志轮转大小 | `logging.basicConfig` | `1 MB` | 超过自动清空，保留 1 个备份 |

> ⚠️ `FAILSAFE = False` 意味着 **没有紧急停止鼠标**，只能用 `Ctrl+C` 退出。如果不小心失控，可快速打开任务管理器结束 Python 进程。

---

## 🛡️ 安全提示 / Safety & Warnings

- **注册表模式会修改系统级设置**，虽然脚本提供 `987789` 一键恢复，但建议运行前先创建系统还原点。
- **`FAILSAFE = False`** 关闭了 pyautogui 的鼠标失效保护，鼠标不会因移到屏幕角落而停止。如果脚本失控，请用任务管理器结束 `python.exe`。
- **窗口监控会自动关闭任何匹配关键词的 `#32770` 对话框**，如果你有正常工作的程序恰好用了标准对话框且标题包含 `runtime / library / host` 等词，可能会被误关。可在 `报错点击.py` 的 `error_keywords` 列表里调整关键词。
- **图像识别点击会真的移动并点击鼠标**，运行期间请勿占用鼠标，重要工作先保存。
- 本工具**仅用于合法的个人自动化场景**（自动化测试、无人值守批处理、辅助无障碍操作等）。请勿用于规避软件授权验证、自动化点击他人系统等非授权场景。

---

## 🐛 常见问题 / FAQ

**Q：`locateOnScreen` 抛 `ImageNotFoundException`？**
A：检查 (1) `ocr/` 下是否真的有 PNG；(2) 是否安装了 `opencv-python`（`confidence` 参数依赖它）；(3) 屏幕分辨率/DPI 是否和截图时一致。

**Q：注册表模式提示"需要管理员权限"？**
A：右键 `python.exe` 或打包后的 `exe` → "以管理员身份运行"。或用 `以管理员身份运行.bat`（需自行创建 `powershell -Command "Start-Process python -ArgumentList '报错点击.py' -Verb RunAs"`）。

**Q：监控模式抓不到 VC++ 运行时错误窗口？**
A：可能该窗口的标题不含 `visual / c++ / runtime / library / host` 关键词，或不是标准 `#32770` 对话框。用 Visual Studio 的 Spy++ 查看实际类名和标题，更新 `error_keywords` / `blacklist_classes`。

**Q：Windows 更新后注册表设置失效了？**
A：Windows 大版本更新会重置部分 WER 设置，重新跑一次 `报错点击.py` 选项 1 即可。

**Q：可以在 macOS / Linux 跑吗？**
A：`default.py` / `继续点击.py` / `简单点击.py` / `截图工具.py` / `test_ocr.py` 只依赖 pyautogui，理论可跨平台。`报错点击.py` 强依赖 `winreg` / `ctypes.windll` / `msvcrt`，**只能在 Windows 运行**。

---

## 🤝 贡献 / Contributing

欢迎提 Issue / PR。请遵守：

1. Fork → 新建分支 → 提 PR
2. Python 代码保持 4 空格缩进、UTF-8 编码、文件头保留 `#!/usr/bin/env python3` 与 `# -*- coding: utf-8 -*-`
3. 不要把 `venv/` `build/` `dist/` `*.exe` `*.log` 提交进来（`.gitignore` 已排除）
4. **`ocr/` 下的图片资源是仓库必需品，请勿删除**

---

## 📜 更新日志 / Changelog

- **v4.0** (`default.py`) — 自动发现 `ocr/` 下所有按钮图，随机选择点击，避免重复点同一个
- **v3.0** (`继续点击.py`) — 固定 4 张 `continue_button*.png` 模板
- **v2.0** (`报错点击.py`) — 注册表 + 窗口监控双模式，隐藏恢复入口，彩色 UI
- **v1.0** — 简单坐标点击工具

---

## 📄 许可证 / License

本项目基于 [MIT License](./LICENSE) 开源，版权所有 © 2026 feichenxi。

依赖库遵循各自许可证：[PyAutoGUI (BSD-3)](https://github.com/asweigart/pyautogui)、[OpenCV (Apache-2.0)](https://opencv.org/)、[NumPy (BSD-3)](https://numpy.org/)。

---

## 📬 联系方式

如有问题、建议或合作意向，欢迎通过以下方式联系我：

- **邮箱**：[44998076@qq.com](mailto:44998076@qq.com)
- **微信**：扫描下方二维码

![微信二维码](qrcode.png)

---

## ⚠️ 免责声明

本项目仅供学习和研究目的。请遵守当地法律法规，在合法合规的前提下使用。作者不对任何不当使用行为承担责任。

---

<div align="center">

**⭐ 如果 AI writes code and automatically clicks 帮你少守了一晚上电脑，给个 Star 吧 ⭐**

*Stay Safe, Stay Secure — 感谢使用！*

</div>
