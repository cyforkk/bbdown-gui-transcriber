# BBDown GUI 下载与转文字工具

这是一个基于 `uv` 管理的 Python/Tkinter 桌面工具，集成：

- BBDown 收藏夹/单视频下载 GUI
- Faster-Whisper 音频/视频转文字
- Windows 单文件 exe 打包
- 同目录 `bbdown.exe` 自动检测

## 推荐使用

普通用户运行：

```text
release\BilibiliDownloaderUI.exe
```

如果不想安装或配置 BBDown，可以把 `bbdown.exe` 放到同一个目录：

```text
release\
├─ BilibiliDownloaderUI.exe
├─ bbdown.exe                  # 可选，放这里会被自动识别
└─ README.txt
```

GUI 检测 BBDown 的顺序：

1. exe 同目录的 `bbdown.exe`
2. 源码运行时项目根目录的 `bbdown.exe`
3. 系统 PATH 中的 `bbdown`
4. 用户手动点击 `选择 bbdown`

## 当前目录结构

```text
D:\bbdown脚本\
├─ src\
│  └─ bbdown_gui\
│     ├─ __init__.py
│     ├─ app.py                # Tkinter GUI
│     ├─ downloader.py         # BBDown 下载逻辑
│     └─ transcriber.py        # Faster-Whisper 转文字逻辑
├─ tests\
│  ├─ test_app.py
│  ├─ test_downloader.py
│  └─ test_transcriber.py
├─ scripts\
│  └─ build_exe.py
├─ docs\
│  ├─ 功能总和文档.md
│  └─ 问题总和文档.md
├─ release\
│  ├─ BilibiliDownloaderUI.exe
│  └─ README.txt
├─ README.md
├─ pyproject.toml
├─ uv.lock
├─ .python-version
└─ .gitignore
```

## 环境准备

首次拉取项目后执行：

```bat
uv sync
```

源码运行 GUI：

```bat
uv run python -m bbdown_gui.app
```

或：

```bat
uv run bbdown-gui
```

## 功能说明

### 下载功能

- 收藏夹批量下载
- 单个视频链接 / BV 号下载
- 音频 / 视频二选一
- 选择下载目录
- 自动检测或手动选择 BBDown
- 停止下载
- 隐藏 BBDown 子进程 CMD 窗口

### 转文字功能

- 单个音频/视频文件转文字
- 文件夹批量转文字
- 支持 `.m4a`、`.mp3`、`.wav`、`.flac`、`.aac`、`.mp4`
- `.mp4` 视频转文字识别的是视频里的音频流，不是画面 OCR
- 默认模型：`medium`
- 默认设备：`cuda`
- 默认计算类型：`int8_float16`
- 输出同名 `.txt`
- 支持停止任务

## 批量转文字说明

选择文件夹批量转文字时，Faster-Whisper 模型只加载一次，后续文件复用同一个模型实例。

```text
加载模型 1 次
处理文件 1
处理文件 2
处理文件 3
...
```

如果某个文件损坏或没有识别到文字，不会中断整个批量任务，会在最终统计里列出失败原因。

## 视频转文字说明

视频转文字流程：

```text
视频文件 -> 读取音频流 -> Faster-Whisper 语音识别 -> 输出 txt
```

不支持：

- 识别画面文字
- OCR
- 无音频流视频

## 运行测试

```bat
uv run python -m unittest discover -s tests
```

## 打包 exe

```bat
uv run python scripts\build_exe.py
```

生成：

```text
dist\BilibiliDownloaderUI.exe
```

发布版复制到：

```text
release\BilibiliDownloaderUI.exe
```

当前包含 Faster-Whisper 依赖后的 exe 约 91.58 MB。exe 不包含 BBDown 本体。

## 常见问题

### 找不到 BBDown

把 `bbdown.exe` 放到 `BilibiliDownloaderUI.exe` 同目录，或在 GUI 中点击 `选择 bbdown`。

### 首次转文字很慢

Faster-Whisper 首次加载模型或下载模型缓存可能较慢，属于正常现象。

### 视频转文字没有结果

确认视频有音频流。当前不会识别画面字幕或画面文字。
