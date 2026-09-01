# GitHub Release 发布说明

> 当前项目已改为源码运行优先，不再推荐上传 1GB+ 的完整 Windows Release 包。本文档保留 GitHub Release 的概念和可选操作说明，仅供需要自行发布的人参考。

## gh 是什么

`gh` 是 GitHub 官方提供的命令行工具，全称是 GitHub CLI。

它可以在终端里操作 GitHub，例如：

- 查看仓库
- 创建 issue
- 创建 pull request
- 创建 release
- 上传 release 附件

本项目里提到的“gh 上传创建 release”，指的是使用 `gh release create` 命令创建 GitHub Release，并上传打包好的 zip 文件。

## GitHub Release 是什么

GitHub Release 是 GitHub 仓库里的“版本发布”功能。

源码代码通过 git 管理，例如：

```text
src/
tests/
docs/
README.md
pyproject.toml
uv.lock
```

软件成品通过 Release 发布，例如：

```text
BilibiliDownloaderUI-windows-x64-v0.2.1.zip
```

本项目当前不再推荐上传大体积 Release 包；普通用户更推荐按照 README 使用 `uv sync` 和 `uv run bbdown-gui` 源码运行。

## git push 和 GitHub Release 的区别

### git push

`git push` 上传的是源码和文档。

适合上传：

```text
src/
tests/
docs/
scripts/
README.md
pyproject.toml
uv.lock
```

不适合上传大型二进制发布包。

### GitHub Release

GitHub Release 上传的是用户可以直接下载的软件成品。

适合上传：

```text
BilibiliDownloaderUI-windows-x64-v0.2.1.zip
```

也就是打包后的 Windows 程序。

## 为什么本项目不把 release 提交进 git

本项目的文件夹版发布包包含：

- Python 运行环境依赖
- Tkinter 运行数据
- Faster-Whisper
- CUDA 相关 DLL
- cuBLAS
- cuDNN
- onnxruntime
- numpy 等依赖

这些文件体积很大。

如果把 `release/` 目录提交进 git，会导致：

1. 仓库体积巨大。
2. `git clone` 很慢。
3. `git push` 容易失败。
4. GitHub 可能拒绝超大文件。
5. 后续每次更新 release 都会让 git 历史越来越臃肿。

所以本项目采用：

```text
源码 -> git push
发布包 -> GitHub Releases
```

## 可选：本项目发布文件

如果确实需要自行发布 Windows 文件夹版，可以将本地生成的发布目录：

```text
release\BilibiliDownloaderUI\
```

压缩成：

```text
BilibiliDownloaderUI-windows-x64-v0.2.1.zip
```

zip 内部结构应类似：

```text
BilibiliDownloaderUI\
├─ BilibiliDownloaderUI.exe
└─ _internal\
```

注意：不要只压缩 `BilibiliDownloaderUI.exe`，必须压缩整个 `BilibiliDownloaderUI` 文件夹。

## 手动创建 GitHub Release

如果不使用 `gh`，可以在 GitHub 网页上手动创建 Release。

步骤：

1. 打开项目仓库页面。
2. 点击右侧或顶部的 `Releases`。
3. 点击 `Draft a new release`。
4. 填写 tag：

   ```text
   v0.2.1
   ```

5. 填写 release title：

   ```text
   BilibiliDownloaderUI v0.2.1
   ```

6. 上传附件：

   ```text
   BilibiliDownloaderUI-windows-x64-v0.2.1.zip
   ```

7. 填写 release notes。
8. 点击发布。

## 使用 gh 创建 GitHub Release

如果电脑已经安装 GitHub CLI，并且已经登录 GitHub，可以使用命令创建 Release。

示例：

```bash
gh release create v0.2.1 BilibiliDownloaderUI-windows-x64-v0.2.1.zip \
  --title "BilibiliDownloaderUI v0.2.1" \
  --notes "修复文件夹版启动失败和下载假成功问题。"
```

这个命令会做三件事：

1. 创建 tag / release：

   ```text
   v0.2.1
   ```

2. 设置标题：

   ```text
   BilibiliDownloaderUI v0.2.1
   ```

3. 上传 zip 附件：

   ```text
   BilibiliDownloaderUI-windows-x64-v0.2.1.zip
   ```

## 检查 gh 是否可用

可以执行：

```bash
gh --version
```

如果提示：

```text
gh: command not found
```

说明当前环境没有安装 GitHub CLI。

可以选择手动在网页上传 Release，也可以先安装 GitHub CLI。

## 检查 gh 是否已登录

执行：

```bash
gh auth status
```

如果未登录，可以执行：

```bash
gh auth login
```

然后按提示完成 GitHub 登录。

## v0.2.1 Release Notes 建议

```markdown
## 修复内容

- 修复文件夹版启动失败问题
  - 修复 `_internal/_tcl_data` 或 `_internal/_tk_data` 缺失导致 Tkinter 启动失败的问题
  - 构建脚本现在会在打包完成后校验必要运行数据是否存在

- 修复下载“假成功”问题
  - 旧版本只根据 BBDown 退出码判断下载成功
  - 新版本会在下载前后检测目标目录新增文件
  - 如果 BBDown 返回成功但没有生成文件，会提示：`BBDown 执行完成，但未检测到下载文件`

- 优化下载日志
  - 下载成功时会显示实际生成的文件路径

## 使用方式

下载：

```text
BilibiliDownloaderUI-windows-x64-v0.2.1.zip
```

解压后双击：

```text
BilibiliDownloaderUI\BilibiliDownloaderUI.exe
```

注意：这是文件夹版发布包，请保持整个 `BilibiliDownloaderUI` 文件夹完整，不要只复制 exe。

## BBDown 说明

本发布包不内置 BBDown。

可以通过以下方式使用 BBDown：

1. 系统 PATH 中已有 `bbdown`
2. 在 GUI 中点击“选择 bbdown”
3. 将可独立运行的 `bbdown.exe` 放到 `BilibiliDownloaderUI.exe` 同目录

注意：`.NET global tool` 安装目录复制出来的 `bbdown.exe` 通常不能当便携版使用，推荐保留原始安装路径并让程序从 PATH 自动检测。
```

## 可选发布流程总结

如果维护者仍然选择发布 zip，可以按以下流程操作：

1. 提交源码：

   ```bash
   git add .
   git commit -m "中文提交信息"
   git push
   ```

2. 本地打包：

   ```bat
   uv run python scripts\build_exe.py
   ```

3. 压缩发布目录：

   ```text
   dist\BilibiliDownloaderUI\ -> BilibiliDownloaderUI-windows-x64-v0.2.1.zip
   ```

4. 上传到 GitHub Releases。

但当前项目默认不推荐上传超大 zip，优先建议用户源码运行。


## 为什么自己压缩的 zip 和工具压缩的 zip 大小不同

同一个发布目录，使用不同方式压缩后，zip 文件大小可能不完全一样，这是正常现象。

常见原因如下。

### 1. 压缩层级不同

推荐压缩的是这个文件夹：

```text
release\BilibiliDownloaderUI\
```

正确 zip 打开后第一层应该是：

```text
BilibiliDownloaderUI\
├─ BilibiliDownloaderUI.exe
└─ _internal\
```

如果压缩的是整个 `release` 目录，zip 里可能变成：

```text
release\
├─ BilibiliDownloaderUI\
│  ├─ BilibiliDownloaderUI.exe
│  └─ _internal\
└─ README.txt
```

如果直接进入 `BilibiliDownloaderUI` 文件夹后全选内容压缩，zip 里可能变成：

```text
BilibiliDownloaderUI.exe
_internal\
```

这几种结构不同，压缩包大小也可能不同。

### 2. 是否包含额外文件

如果压缩整个 `release` 目录，可能会额外包含：

```text
README.txt
desktop.ini
旧 zip 文件
临时文件
```

这些文件会让压缩包大小发生变化。

本项目上传 GitHub Releases 时，推荐只上传 `BilibiliDownloaderUI` 文件夹本身，不要把外层 `release` 目录一起压进去。

### 3. 压缩工具和压缩等级不同

不同压缩工具生成的 zip 大小可能不同，例如：

- Windows 右键“发送到压缩文件夹”
- 7-Zip
- WinRAR
- Bandizip
- Python `zipfile`

即使文件完全一样，不同工具的压缩算法、压缩等级、元数据处理方式也可能不同。

所以 zip 大小不一致，不一定代表内容错误。

### 4. 文件版本是否一致

如果一个 zip 是修复前压缩的，另一个 zip 是修复后压缩的，大小也会不同。

例如本项目曾修复过：

- `_tcl_data` / `_tk_data` 缺失导致启动失败
- 下载成功但目录为空的假成功问题
- CUDA/Faster-Whisper 依赖打包问题

这些修复可能导致发布目录内容发生变化。

### 5. 推荐压缩方式

进入目录：

```text
D:\bbdown脚本\release
```

只选中：

```text
BilibiliDownloaderUI
```

压缩成：

```text
BilibiliDownloaderUI-windows-x64-v0.2.1.zip
```

最终 zip 内部结构应该是：

```text
BilibiliDownloaderUI\
├─ BilibiliDownloaderUI.exe
└─ _internal\
```

### 6. 判断标准

压缩包大小可以有差异，重点看三点：

1. zip 内部第一层是否是 `BilibiliDownloaderUI` 文件夹。
2. `BilibiliDownloaderUI.exe` 和 `_internal` 是否都在里面。
3. 解压后双击 `BilibiliDownloaderUI\BilibiliDownloaderUI.exe` 是否可以正常启动和使用。

只要这三点满足，压缩包大小略有差异通常没有问题。

## 用 gh 快速发布（手动 / 重跑）

GitHub CLI 可以本地创建 tag + 上传产物，无需等 CI。适合本地手动发布或 CI 失败后重跑。

### 前置

```bash
gh --version
gh auth login
gh auth status
```

### 本地手动打包并发布

```bash
cd d:\bbdown脚本
uv run python scripts\build_exe.py --edition lite

$tag = "v0.2.3"
Compress-Archive -Path dist\BilibiliDownloaderUI -DestinationPath BilibiliDownloaderUI-windows-x64-$tag.zip

gh release create $tag BilibiliDownloaderUI-windows-x64-$tag.zip ^
  --title "BilibiliDownloaderUI $tag" ^
  --generate-notes
```

`-generate-notes` 让 GitHub 按 commit 自动生成 release notes，可后续在网页手动编辑。

### 已存在 tag，只想补传产物

```bash
gh release upload v0.2.3 BilibiliDownloaderUI-windows-x64-v0.2.3.zip --clobber
```

### 触发 CI 用现有 tag 重跑

默认分支上已有 workflow 文件时，可以用 `workflow_dispatch` 用指定 tag 重跑：

```bash
gh workflow run Release -f tag=v0.2.3
```

或加 `-f skip_version_check=true` 跳过 tag 与 pyproject 版本一致性校验（紧急发版时使用）。

### 查看流水线与日志

```bash
gh run list --workflow=Release
gh run watch
gh run view <run-id> --log-failed
```
