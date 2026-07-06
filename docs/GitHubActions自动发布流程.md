# GitHub Actions 自动发布流程

> 本文档记录通过 GitHub Actions 自动构建 Windows lite 版并发布到 GitHub Release 的流程。

## 设计目标

- 推送 `v*` 版本标签时自动触发构建
- 只构建 **lite 版**（仅下载功能，不含 CUDA / Faster-Whisper 等大依赖，体积可控）
- 自动生成 zip 产物并上传到对应 tag 的 Release
- 构建成功才创建 / 更新 Release，避免出现空 Release

## 为什么只发 lite 版

full 版包含 Faster-Whisper、CUDA、cuBLAS、cuDNN、onnxruntime 等大文件，压缩后仍可能超过 1GB，CI 上传下载不稳定，且 GitHub Release 单文件有 2GB 上限。因此：

- **lite 版**：CI 自动构建发布（体积约几十 MB）
- **full 版**：维护者本地打包发布，流程见 [GitHubRelease发布说明.md](GitHubRelease发布说明.md)

## 工作流文件

位置：`.github/workflows/release.yml`

触发条件：

```yaml
on:
  push:
    tags:
      - 'v*'
```

权限声明：

```yaml
permissions:
  contents: write
```

显式声明 `contents: write` 后，`GITHUB_TOKEN` 即可创建 Release 并上传产物，**无需**在 GitHub 网页手动修改 Workflow permissions 设置。

## 构建步骤

1. `actions/checkout@v4` 拉取代码
2. `astral-sh/setup-uv@v5` 安装 uv
3. `uv sync` 安装运行依赖（不含 transcribe extra，即 lite 配置）
4. `uv run python scripts/build_exe.py --edition lite` 打包 Windows 文件夹版
5. PowerShell `Compress-Archive` 将 `dist/BilibiliDownloaderUI` 压缩为 zip
6. `softprops/action-gh-release@v2` 将 zip 上传到 tag 对应的 Release，并自动生成 release notes

## 产物

- 文件名：`BilibiliDownloaderUI-windows-x64-vX.Y.Z.zip`
- zip 内部结构：

```text
BilibiliDownloaderUI\
├─ BilibiliDownloaderUI.exe
└─ _internal\
```

- 解压后双击 `BilibiliDownloaderUI\BilibiliDownloaderUI.exe` 启动

## 发布新版本流程

```bash
# 1. 确保所有改动已提交并推送到 main
git add .
git commit -m "feat: 描述"
git push

# 2. 打版本标签并推送（触发 CI）
git tag v0.2.2
git push origin v0.2.2

# 3. 查看 CI 进度
gh run list

# 4. 失败时查看日志
gh run view <run-id> --log-failed
```

CI 成功后，Release 页面会自动出现 `v0.2.2` 及其 zip 附件。release notes 由 GitHub 根据 commits 自动生成，可后续在网页手动编辑。

## 注意事项

- **不要推 `v*` 前缀的非版本标签**，例如 `v-test`，会误触发 CI。临时标签用其他前缀（如 `dev-`）。
- lite 版**不包含转文字功能**。用户如需转文字，应按 README 使用 `uv sync --extra transcribe` 源码运行，或维护者本地打包 full 版。
- 打包脚本 `scripts/build_exe.py` 在打包完成后会校验 `_tcl_data` / `_tk_data` 等 Tkinter 运行数据是否存在，缺失则构建失败，避免发布启动即崩溃的 exe。
- Windows runner 默认控制台编码为 cp1252，`build_exe.py` 的中文 `print` 会触发 `UnicodeEncodeError`。工作流已通过 job 级别 `env: PYTHONUTF8: '1'` 启用 Python UTF-8 模式解决，修改源码时无需顾虑。
- `pyproject.toml` 中默认 index 为清华镜像，CI（境外 runner）也能访问；若 CI 因镜像不稳定失败，可在工作流中用 `UV_INDEX_URL` 环境变量覆盖为 `https://pypi.org/simple`。
- full 版仍需本地手动发布，流程不变，见 [GitHubRelease发布说明.md](GitHubRelease发布说明.md)。

## 与现有发布方式的关系

| 场景 | 方式 | 文档 |
|---|---|---|
| lite 版（仅下载） | CI 自动发布 | 本文档 |
| full 版（含转文字） | 维护者本地打包手动上传 | GitHubRelease发布说明.md |
| 源码运行 | 用户 `uv sync` + `uv run bbdown-gui` | README.md |

三种方式互补，不冲突。
