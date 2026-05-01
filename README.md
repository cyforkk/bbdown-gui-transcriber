# BBDown 哔哩哔哩下载工具

这是一个基于 `uv` 管理的 Python/Tkinter 工具，支持：

- GUI 图形界面
- BBDown 下载收藏夹或单个视频
- Faster-Whisper 音频/视频转文字

## 推荐运行方式

源码验证阶段推荐使用 uv 运行 GUI：

```bat
uv run python "D:\bbdown脚本\bilibili_downloader_ui.py"
```

当前 release exe 仍是上一版下载器。转文字功能先在源码 GUI 中验证，确认稳定后再处理 exe 打包。

## 环境说明

项目使用 uv 管理环境：

```text
pyproject.toml
uv.lock
.python-version
.venv\
```

首次同步：

```bat
uv sync
```

依赖包括：

- `faster-whisper`
- `nvidia-cublas-cu12`
- `nvidia-cudnn-cu12`
- `pyinstaller`（开发依赖）

## GUI 功能

### 下载功能

- 收藏夹批量下载。
- 单个视频链接 / BV 号下载。
- 音频 / 视频二选一。
- 选择下载目录。
- 自动检测或手动选择 BBDown。
- 停止下载。
- 隐藏 BBDown 子进程 CMD 窗口。

### 转文字功能

- 选择单个音频/视频文件转文字。
- 选择文件夹批量转文字。
- 支持格式：`.m4a`、`.mp3`、`.wav`、`.flac`、`.aac`、`.mp4`。
- 视频转文字支持 `.mp4`，本质是识别视频文件里的音频流，不是识别画面文字或 OCR。
- 默认模型：`medium`。
- 默认设备：`cuda`。
- 默认计算类型：`int8_float16`。
- 输出同名 `.txt` 文件。
- 支持停止任务。

## 视频转文字说明

当前支持 `.mp4` 视频转文字，但识别对象是视频中的声音：

```text
视频文件 -> 读取音频流 -> Faster-Whisper 语音识别 -> 输出 txt
```

不支持的场景：

- 不会识别画面中的文字。
- 不会对视频画面做 OCR。
- 如果视频没有音频流，会提示：
  ```text
  媒体文件中没有可识别的音频流
  ```
- 如果视频文件损坏，会提示：
  ```text
  媒体文件无效
  ```

批量选择文件夹时，`.mp4` 会和 `.m4a`、`.mp3` 等音频文件一起被扫描并处理。

## 使用步骤

### 下载收藏夹音频

1. 运行 GUI。
2. 在 `下载功能` 中选择 `收藏夹链接`。
3. 输入收藏夹链接。
4. 选择 `音频`。
5. 选择下载目录。
6. 点击 `开始下载`。

### 单个视频下载

1. 在 `下载功能` 中选择 `单个视频链接 / BV号`。
2. 输入视频链接或 BV 号。
3. 选择 `音频` 或 `视频`。
4. 点击 `开始下载`。

### 音频文件转文字

1. 在 `转文字功能` 中点击 `选择文件`。
2. 选择 `.m4a`、`.mp3`、`.wav`、`.flac` 或 `.aac` 文件。
3. 保持默认模型参数，或按需修改。
4. 点击 `开始转文字`。
5. 结果会输出到同目录同名 `.txt` 文件。

### 视频文件转文字

1. 在 `转文字功能` 中点击 `选择文件`。
2. 选择包含音频流的 `.mp4` 文件。
3. 点击 `开始转文字`。
4. 结果会输出到同目录同名 `.txt` 文件。

说明：这里识别的是视频里的声音，不是画面字幕。

### 文件夹批量转文字

1. 在 `转文字功能` 中点击 `选择文件夹`。
2. 选择包含音频/视频文件的目录。
3. 点击 `开始转文字`。
4. 每个支持的文件会生成同名 `.txt`。

批量转换时模型只加载一次，后续文件会复用同一个 Faster-Whisper 模型实例，不会每个文件都重新加载模型。

## 运行测试

```bat
uv run python "D:\bbdown脚本\test_download_bilibili_fav.py"
uv run python "D:\bbdown脚本\test_bilibili_downloader_ui.py"
uv run python "D:\bbdown脚本\test_audio_transcriber.py"
```

## 重新打包 exe

当前不建议立即打包包含 Faster-Whisper 的 exe，因为 CUDA、模型缓存和依赖体积需要单独验证。

下载器旧版打包命令仍保留：

```bat
uv run python "D:\bbdown脚本\build_exe.py"
```

## 重要说明

- exe 不包含 BBDown。
- 转文字依赖 CUDA 版本的 faster-whisper 环境。
- 如果转文字启动时加载模型较慢，属于正常现象。
- 首次使用模型可能需要下载模型缓存。
- 视频转文字只识别音频流，不识别画面内容。
