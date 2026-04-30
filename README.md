# BBDown 哔哩哔哩下载工具

这是一个基于本机 `BBDown` 的 Python/Tkinter 下载工具，支持 GUI、命令行脚本和 exe 版本。

## 推荐使用

最终用户推荐直接运行：

```text
release\BilibiliDownloaderUI.exe
```

## 当前目录结构

```text
D:\bbdown脚本\
├─ release\
│  └─ BilibiliDownloaderUI.exe      # 推荐分发/使用的最终 exe
├─ dist\
│  └─ BilibiliDownloaderUI.exe      # PyInstaller 原始输出 exe
├─ download_bilibili_fav.py         # Python 核心下载逻辑
├─ bilibili_downloader_ui.py        # Tkinter GUI 源码
├─ build_exe.py                     # exe 打包脚本
├─ test_download_bilibili_fav.py    # 核心逻辑测试
├─ test_bilibili_downloader_ui.py   # GUI 支撑测试
├─ README.md                        # 使用说明
├─ 功能总和文档.md                  # 功能记录
└─ 问题总和文档.md                  # 问题记录
```

## 重要说明

exe **不包含 BBDown**。

目标电脑仍然需要：

- 已安装 BBDown，并且能通过 `bbdown` 命令调用；或
- 在 GUI 中手动选择 `bbdown.exe`。

## 直接运行 exe

双击运行：

```text
D:\bbdown脚本\release\BilibiliDownloaderUI.exe
```

如果 GUI 没有自动检测到 BBDown：

1. 点击 `自动检测`。
2. 如果仍未检测到，点击 `选择 bbdown`。
3. 手动选择 `bbdown.exe`。

## GUI 功能

- 收藏夹批量下载。
- 单个视频链接 / BV 号下载。
- 音频 / 视频二选一。
- 选择下载目录。
- 自动检测或手动选择 BBDown。
- 开始下载。
- 停止下载。
- 日志窗口实时显示 BBDown 输出。
- 下载完成后显示统计信息。

## 停止下载

如果发现下载错了视频，可以点击：

```text
停止下载
```

停止后：

- 当前正在运行的 BBDown 进程会被终止。
- 收藏夹批量下载不会继续下载下一个视频。
- 日志会显示停止信息。
- 状态变为 `已停止`。
- `开始下载` 按钮恢复可点击。

## GUI 下载收藏夹音频

1. 选择 `收藏夹链接`。
2. 输入收藏夹链接。
3. 选择 `音频`。
4. 选择下载目录，例如：

```text
G:\默认收藏夹\音频
```

5. 点击 `自动检测` 或手动选择 `bbdown.exe`。
6. 点击 `开始下载`。

## GUI 下载单个视频音频

1. 选择 `单个视频链接 / BV号`。
2. 输入视频链接或 BV 号，例如：

```text
https://www.bilibili.com/video/BV1tkdVB4EpP/
```

或者：

```text
BV1tkdVB4EpP
```

3. 选择 `音频` 或 `视频`。
4. 选择下载目录。
5. 点击 `开始下载`。

## 从源码运行 GUI

```bash
python "D:\bbdown脚本\bilibili_downloader_ui.py"
```

## 重新打包 exe

执行：

```bash
python "D:\bbdown脚本\build_exe.py"
```

生成：

```text
D:\bbdown脚本\dist\BilibiliDownloaderUI.exe
```

发布版位置：

```text
D:\bbdown脚本\release\BilibiliDownloaderUI.exe
```

## 运行测试

```bash
python "D:\bbdown脚本\test_download_bilibili_fav.py"
python "D:\bbdown脚本\test_bilibili_downloader_ui.py"
```

## 常见问题

### 1. exe 打开后找不到 BBDown

原因：exe 不包含 BBDown。

处理方式：

- 点击 `自动检测`。
- 如果仍未检测到，点击 `选择 bbdown`，手动选择 `bbdown.exe`。
- 或者把 BBDown 加入系统 PATH。

### 2. 获取收藏夹失败

可能原因：

- 没有登录。
- 收藏夹是私有的。
- 收藏夹不存在。
- 收藏夹链接里的 `fid` 不正确。
- 网络无法访问哔哩哔哩接口。

处理方式：

```bash
bbdown login
```

如果收藏夹是私有的，请先在哔哩哔哩中公开收藏夹。

### 3. 下载目录里没有文件

Windows 上建议使用原生路径：

```text
G:\默认收藏夹\音频
```

不要写成：

```text
/g/默认收藏夹/音频
```

### 4. 下载时弹出 CMD 窗口

新版 GUI 已隐藏 BBDown 子进程窗口。如果仍然弹窗，请确认你运行的是：

```text
D:\bbdown脚本\release\BilibiliDownloaderUI.exe
```

### 5. GUI 日志中文乱码

GUI 已按系统首选编码读取 BBDown 输出，并在日志中显示当前编码。
