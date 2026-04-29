# BBDown 哔哩哔哩下载脚本

这是一个基于本机 `BBDown` 的 Python 跨平台下载脚本，支持两种下载来源：

- 收藏夹批量下载
- 单个视频下载

主脚本：

```text
download_bilibili_fav.py
```

## 功能

- 根据哔哩哔哩收藏夹链接自动解析 `fid`。
- 自动分页获取收藏夹内全部视频。
- 支持单个视频链接或 BV 号下载。
- 支持音频/视频二选一下载：
  - `audio`：只下载音频。
  - `video`：下载视频。
- 支持指定下载目录。
- 收藏夹批量下载时，单个视频失效或下载失败会自动跳过，不中断后续任务。
- 下载完成后输出统计信息：总数、成功数、失败数、失败列表。
- 提供 Python 单元测试。

## 环境要求

### 1. Python

需要安装 Python。

检查命令：

```bash
python --version
```

如果系统中 Python 命令是 `python3`，后续命令可把 `python` 替换为 `python3`。

### 2. BBDown

需要本机已安装 `BBDown`，并且命令行可以直接调用 `bbdown`。

检查命令：

```bash
bbdown --help
```

如果提示找不到命令，需要先安装 BBDown，并确保它已加入系统 PATH。

### 3. 登录说明

如果收藏夹需要登录权限，或者下载会员/受限内容，先执行：

```bash
bbdown login
```

按 BBDown 提示扫码登录即可。

## 使用方式

下载来源二选一：

| 来源 | 参数 | 说明 |
| --- | --- | --- |
| 收藏夹 | `--fav-url` | 批量下载收藏夹内全部视频 |
| 单个视频 | `--video-url` | 下载一个视频链接或 BV 号 |

`--fav-url` 和 `--video-url` 不能同时使用，也不能都不传。

通用参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--mode` | 是 | 下载模式，只能是 `audio` 或 `video` |
| `--output-dir` | 是 | 下载目录 |

## 收藏夹批量下载

### Windows CMD 下载音频

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" --fav-url "https://space.bilibili.com/619278616/favlist?fid=3928433616&ftype=create" --mode audio --output-dir "G:\默认收藏夹\音频"
```

### Windows CMD 下载视频

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" --fav-url "https://space.bilibili.com/619278616/favlist?fid=3928433616&ftype=create" --mode video --output-dir "G:\默认收藏夹\视频"
```

### Linux/macOS 下载音频

```bash
python download_bilibili_fav.py \
  --fav-url "https://space.bilibili.com/619278616/favlist?fid=3928433616&ftype=create" \
  --mode audio \
  --output-dir "/home/user/bilibili-audio"
```

## 单个视频下载

### Windows CMD 下载单个视频的音频

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" --video-url "https://www.bilibili.com/video/BV1tkdVB4EpP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=9e9edf796dae1e9ced58ec1bdbd37c73" --mode audio --output-dir "G:\默认收藏夹\音频"
```

### Windows CMD 下载单个完整视频

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" --video-url "https://www.bilibili.com/video/BV1tkdVB4EpP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=9e9edf796dae1e9ced58ec1bdbd37c73" --mode video --output-dir "G:\默认收藏夹\视频"
```

### 直接使用 BV 号

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" --video-url "BV1tkdVB4EpP" --mode audio --output-dir "G:\默认收藏夹\音频"
```

### Linux/macOS 下载单个视频音频

```bash
python download_bilibili_fav.py \
  --video-url "https://www.bilibili.com/video/BV1tkdVB4EpP/" \
  --mode audio \
  --output-dir "/home/user/bilibili-audio"
```

## 音频和视频模式区别

### 音频模式

```bash
--mode audio
```

脚本会调用：

```bash
bbdown BV号 --audio-only --work-dir 下载目录
```

适合保存音频内容。

### 视频模式

```bash
--mode video
```

脚本会调用：

```bash
bbdown BV号 --work-dir 下载目录
```

适合保存完整视频。

## Windows CMD 多行写法说明

CMD 使用 `^` 作为换行符，例如：

```bat
python "D:\bbdown脚本\download_bilibili_fav.py" ^
  --video-url "BV1tkdVB4EpP" ^
  --mode audio ^
  --output-dir "G:\默认收藏夹\音频"
```

注意：

- `^` 必须放在每一行最后。
- `^` 后面不要有空格。
- 最后一行不要加 `^`。
- 出现 `More?` 是 CMD 等待继续输入，不是脚本报错。

## 运行测试

测试文件：

```text
test_download_bilibili_fav.py
```

运行：

```bash
python test_download_bilibili_fav.py
```

当前测试覆盖：

- 收藏夹链接 `fid` 解析。
- 缺少 `fid` 时抛出错误。
- 单个视频链接 BV 号解析。
- 直接传入 BV 号解析。
- 收藏夹下载和单个视频下载参数互斥。
- 音频模式 BBDown 命令构造。
- 视频模式 BBDown 命令构造。
- 收藏夹接口失败时提示未登录、私有或不存在。
- 批量下载时单个视频失败后跳过。
- 单个视频下载时使用解析出的 BV 号调用 BBDown。

## 常见问题

### 1. 获取收藏夹失败

可能原因：

- 没有登录。
- 收藏夹是私有的。
- 收藏夹不存在。
- 收藏夹链接里的 `fid` 不正确。
- 网络无法访问哔哩哔哩接口。

处理方式：

1. 检查收藏夹链接是否正确。
2. 如果需要登录，先执行：

```bash
bbdown login
```

3. 如果收藏夹是私有的，请先在哔哩哔哩中公开收藏夹。

### 2. 下载目录里没有文件

先确认命令中的 `--output-dir` 是否写对。

Windows 上建议使用原生路径：

```text
G:\默认收藏夹\音频
```

不要把 Windows 盘符目录写成：

```text
/g/默认收藏夹/音频
```

因为 BBDown 是 .NET 程序，在 Windows 环境下可能把 `/g/...` 识别成错误目录。

### 3. 某些视频下载失败

脚本会自动跳过失败视频，并在最后输出失败列表。

常见原因：

- 视频已删除。
- 视频失效。
- 视频需要登录权限。
- 视频有区域限制。
- 当前账号无权限下载。

### 4. 中文路径乱码

Windows 终端可能显示乱码，但只要路径和文件实际存在，一般不影响下载。

如果显示异常，可以尝试使用 Windows Terminal，或在 PowerShell 中执行：

```powershell
chcp 65001
```

### 5. 找不到 bbdown 命令

如果出现类似 `bbdown: command not found`，说明 BBDown 没有加入 PATH。

处理方式：

- 确认 BBDown 已安装。
- 确认命令行能执行：

```bash
bbdown --help
```

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `download_bilibili_fav.py` | Python 跨平台下载脚本 |
| `test_download_bilibili_fav.py` | Python 单元测试 |
| `README.md` | 使用说明文档 |
| `功能总和文档.md` | 功能实现记录 |
| `问题总和文档.md` | 问题和修复记录 |

## 推荐使用流程

1. 确认 BBDown 可用：

```bash
bbdown --help
```

2. 如有权限问题，先登录：

```bash
bbdown login
```

3. 执行 Python 脚本下载收藏夹或单个视频。

4. 查看下载统计和失败列表。
