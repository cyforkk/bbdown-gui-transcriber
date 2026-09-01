# PyInstaller 单文件版和文件夹版区别：为什么 BBDown GUI 改用文件夹版发布

## 背景

BBDown GUI 最初使用 PyInstaller 的单文件模式发布，也就是最终只生成一个：

```text
BilibiliDownloaderUI.exe
```

这种方式看起来最简单，用户只需要复制和双击一个 exe 文件。

但后来项目加入了 Faster-Whisper 转文字功能，并且为了支持 CUDA 加速，打包时还需要带上：

- Faster-Whisper
- CUDA 相关运行库
- cuBLAS
- cuDNN
- onnxruntime
- numpy
- 其他 Python 运行依赖

这些依赖体积很大。单文件版 exe 最终超过 1GB，双击启动时明显变慢。

所以项目最终从 PyInstaller `--onefile` 单文件版改成了 `--onedir` 文件夹版。

## 单文件版是什么

PyInstaller 单文件版使用参数：

```text
--onefile
```

生成结果类似：

```text
release\
└─ BilibiliDownloaderUI.exe
```

用户只需要双击这个 exe。

## 单文件版的启动原理

单文件 exe 并不是所有依赖都直接原地运行。

它更像是一个自解压包：

1. 用户双击 exe。
2. exe 先把内部依赖解压到系统临时目录。
3. 临时目录通常类似：

   ```text
   C:\Users\用户名\AppData\Local\Temp\_MEIxxxxxx
   ```

4. 程序再从这个临时目录启动真正的 Python 应用。

如果程序只有几十 MB，这个过程通常感觉不到。

但如果 exe 超过 1GB，每次启动都要解压大量 DLL、模型依赖和 Python 包，启动就会明显变慢。

## 单文件版的优点

### 1. 分发简单

只有一个文件：

```text
BilibiliDownloaderUI.exe
```

复制、发送、备份都很方便。

### 2. 用户不容易漏文件

因为所有依赖都塞进一个 exe 里，用户不会因为少复制某个 DLL 或目录导致程序无法启动。

### 3. 适合小工具

如果项目只是一个简单 GUI，依赖很少，体积几十 MB 以内，单文件版体验很好。

## 单文件版的缺点

### 1. 大型依赖启动慢

本项目包含 CUDA 和 Faster-Whisper 后，单文件 exe 超过 1GB。

每次启动都需要先解压大体积依赖，所以启动慢。

### 2. 临时目录不固定

每次运行时，依赖会被解压到类似 `_MEIxxxxxx` 的临时目录。

这会增加排查成本，尤其是涉及：

- DLL 加载
- 模型资源文件
- Faster-Whisper assets
- CUDA 运行库

### 3. 杀毒软件可能扫描更久

超大的单文件 exe 更容易被杀毒软件进行完整扫描，进一步拖慢首次启动。

## 文件夹版是什么

PyInstaller 文件夹版使用参数：

```text
--onedir
```

生成结果类似：

```text
release\
└─ BilibiliDownloaderUI\
   ├─ BilibiliDownloaderUI.exe
   └─ _internal\
      ├─ python313.dll
      ├─ faster_whisper\
      ├─ nvidia\
      ├─ onnxruntime\
      ├─ numpy\
      └─ ...
```

用户双击：

```text
release\BilibiliDownloaderUI\BilibiliDownloaderUI.exe
```

## 文件夹版的启动原理

文件夹版在打包阶段就已经把依赖展开到目录里。

启动时不需要再把 1GB 依赖解压到临时目录，而是直接从当前发布目录读取文件。

因此对于大型 AI/CUDA 桌面程序，文件夹版通常比单文件版启动更快。

## 文件夹版的优点

### 1. 启动更快

依赖已经在文件夹里，不需要每次启动都解压整个大包。

这是本项目切换到文件夹版的核心原因。

### 2. DLL 和资源路径更稳定

CUDA、cuBLAS、cuDNN、Faster-Whisper assets 等文件都在固定目录里。

出现问题时，也更容易检查到底缺哪个文件。

### 3. 更适合 AI/CUDA 工具

只要项目包含大型依赖，比如：

- CUDA
- PyTorch
- Faster-Whisper
- onnxruntime
- 大量 DLL
- 大模型相关资源

文件夹版通常比单文件版更稳。

## 文件夹版的缺点

### 1. 发布内容不是一个文件

发布时必须保留整个目录：

```text
BilibiliDownloaderUI\
```

不能只复制里面的：

```text
BilibiliDownloaderUI.exe
```

否则程序可能找不到依赖。

### 2. 文件数量多

文件夹版会有很多依赖文件，看起来没有单文件版整洁。

### 3. 用户需要知道正确入口

正确启动路径是：

```text
release\BilibiliDownloaderUI\BilibiliDownloaderUI.exe
```

而不是旧版的：

```text
release\BilibiliDownloaderUI.exe
```

## 本项目为什么选择文件夹版

BBDown GUI 现在已经不是一个单纯下载器，而是同时包含：

- BBDown 下载 GUI
- 收藏夹批量下载
- 单视频下载
- 音频/视频二选一
- Faster-Whisper 转文字
- 文件夹批量转文字
- CUDA 加速

为了让 release exe 能在没有本地 Python 环境的情况下运行，打包时需要带上 CUDA 相关 DLL。

单文件版虽然方便，但启动太慢。

文件夹版虽然文件更多，但可以避免每次启动重复解压 1GB 以上的依赖，因此更适合当前项目。

## 当前项目的推荐启动方式

现在推荐双击：

```text
release\BilibiliDownloaderUI\BilibiliDownloaderUI.exe
```

如果要放 `bbdown.exe`，也应该放在这个 exe 同目录：

```text
release\
└─ BilibiliDownloaderUI\
   ├─ BilibiliDownloaderUI.exe
   ├─ bbdown.exe
   └─ _internal\
```

注意：不要只复制 `BilibiliDownloaderUI.exe`，需要保持整个 `BilibiliDownloaderUI` 文件夹完整。

## 对比总结

| 对比项 | 单文件版 `--onefile` | 文件夹版 `--onedir` |
|---|---|---|
| 发布形态 | 一个 exe | 一个文件夹 |
| 启动速度 | 大依赖项目较慢 | 更快 |
| 分发便利性 | 最方便 | 需要复制整个文件夹 |
| 用户误操作风险 | 低 | 可能只复制 exe 导致缺文件 |
| DLL/资源排查 | 较麻烦，临时目录变化 | 更直观，文件在固定目录 |
| 适合项目 | 小工具、轻依赖程序 | AI/CUDA/大型依赖程序 |

## 结论

如果只是几十 MB 的小工具，单文件版更方便。

如果项目包含 CUDA、Faster-Whisper、onnxruntime 这类大型依赖，文件夹版更合适。

BBDown GUI 当前选择文件夹版发布，是为了换取更快的启动速度和更稳定的依赖加载体验。


## GitHub 仓库中的发布方式

虽然本项目使用文件夹版发布，但 `release/` 成品不提交到源码仓库。

推荐流程是：

1. 本地运行打包命令生成 `dist/BilibiliDownloaderUI/`。
2. 将整个 `BilibiliDownloaderUI` 文件夹压缩为 `BilibiliDownloaderUI-windows-x64.zip`。
3. 在 GitHub Releases 中上传 zip。
4. 源码仓库只保留代码、文档、测试和打包脚本。

这样既能保留文件夹版启动快的优点，又不会让 git 仓库因为大体积二进制文件变得难以 clone 和 push。

> 具体打包命令、产物结构与验证步骤见 `本地打包指南.md`。
