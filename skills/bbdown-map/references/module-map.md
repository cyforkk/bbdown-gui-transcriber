# 模块边界

BBDown GUI 分四个源码模块加测试。改代码前先确认落在哪个模块，不要越界改别的域。

## src/bbdown_gui/app.py — GUI 主程序

**负责**：Tkinter 界面、事件回调、子进程封装、日志队列、BBDown 自动检测、视频选择弹窗、转文字任务调度。

**不负责**：B 站 API 调用细节、下载分页去重、Whisper 模型加载。

**协作**：调用 `downloader` 拉列表与下载，调用 `transcriber` 转文字；`run_bbdown_command` 把 BBDown 子进程输出灌进日志队列。

## src/bbdown_gui/downloader.py — 下载逻辑

**负责**：收藏夹/合集/单视频链接解析、B 站 API 调用（含 WBI 签名与风控重试）、分页去重、构造 BBDown 命令、`download_all` 批量下载与假成功防护。

**不负责**：GUI、子进程窗口管理、转文字。

**协作**：被 `app.py` 的 `run_fetch_and_select` / `run_download` / `run_download_selected` 调用；`read_json_with_retry` 是所有 B 站 HTTP 请求的统一入口。

## src/bbdown_gui/transcriber.py — 转文字

**负责**：Faster-Whisper 模型加载（`AudioTranscriber`）、ffprobe 预校验、批量转写（`process_media_files`）、CUDA DLL 定位。

**不负责**：下载、GUI 布局。

**协作**：被 `app.py` 的 `run_transcription` 调用；依赖 `transcribe` extra（默认不装）。

## scripts/build_exe.py — 打包

**负责**：构造 PyInstaller 命令、校验发布目录完整性（exe + Tcl/Tk 数据）。

**不负责**：运行时逻辑。

**协作**：CI 与本地打包入口；产物到 `dist/BilibiliDownloaderUI/`。

## tests/ — 测试

**负责**：覆盖 app 检测/弹窗链路、downloader 解析/分页/WBI/命令、transcriber、build_exe。

**不负责**：真实 B 站网络请求（全部 mock）。

## 典型协作关系

- 下载流程：`app.start_download` → `run_fetch_and_select` → `downloader.fetch_*_videos` → `app.handle_video_selection` → `app.run_download_selected` → `downloader.download_all` → `app.run_bbdown_command`。
- 转文字流程：`app.start_transcription` → `run_transcription` → `transcriber.process_media_files`。

## 一个实用判断

- 改"界面行为/弹窗/按钮/日志显示"→ `app.py`。
- 改"拉取不全/接口/签名/分页/命令构造"→ `downloader.py`。
- 改"转文字/模型/CUDA"→ `transcriber.py`。
- 改"打包/发布产物"→ `scripts/build_exe.py`。
