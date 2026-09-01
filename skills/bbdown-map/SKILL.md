---
name: bbdown-map
description: 当需求涉及 BBDown GUI 这个项目本身的代码结构、模块边界、核心数据类、历史踩坑时使用。命中路径：src/bbdown_gui/**、tests/**、scripts/build_exe.py；命中关键字：bbdown_gui、BilibiliDownloaderUI、下载器、转文字、打包、项目熟悉、接手。
---

# bbdown-map

BBDown GUI 项目的结构地图。负责说清"这个项目有哪些模块、各自边界、核心数据类长什么样、历史上踩过哪些坑"。和 `dev-playbook`（通用工作流）的边界：dev-playbook 管怎么做事，bbdown-map 管这个项目长什么样。

## 使用顺序

- 先看 `references/module-map.md`，确认要改的代码落在哪个模块、模块边界在哪。
- 再看 `references/object-dictionary.md`，确认涉及的数据类字段和真相源。
- 涉及历史踩坑或排查怪现象时看 `references/gotchas.md`，并按需翻 `docs/问题总和文档.md`。

## 关键入口

- `src/bbdown_gui/app.py` — GUI 主程序（`BilibiliDownloaderUI`、`main()`、`open_video_selection_dialog`）
- `src/bbdown_gui/downloader.py` — 下载逻辑（解析、拉取列表、`download_all`、WBI 签名）
- `src/bbdown_gui/transcriber.py` — 转文字（`AudioTranscriber`、`process_media_files`）
- `scripts/build_exe.py` — PyInstaller 打包脚本
- `pyproject.toml` — 依赖与入口（`bbdown-gui = bbdown_gui.app:main`）

## 必守约束

- 项目用 `uv` 管理依赖，Python 3.13；转文字依赖在 `transcribe` extra，默认 `uv sync` 不装。
- 改完代码必须 `uv run python -m unittest discover -s tests` 全过再交付。
- 改了 GUI 进程相关代码后，必须重启 GUI 进程才生效，排查"改了没反应"先怀疑旧进程。
- 不内置 BBDown：通过自动检测或用户选择定位 `bbdown.exe`。
- 拉取列表/分页逻辑改动要保持 bvid 去重和以 API 报告总数为目标，不要用短页作终止条件。
- 第三方 B 站 API 调用走 `read_json_with_retry`，友好提示风控，不要让用户配 Cookie。

## 参考资料

- `references/module-map.md`
- `references/object-dictionary.md`
- `references/gotchas.md`
