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

- 推送 `v*` 标签（自动）
- `workflow_dispatch`（手动触发，传入已有 tag 重跑，可选 `skip_version_check` 跳过版本校验）

权限声明：

```yaml
permissions:
  contents: write
```

显式声明 `contents: write` 后，`GITHUB_TOKEN` 即可创建 Release 并上传产物，**无需**在 GitHub 网页手动修改 Workflow permissions 设置。

Runner 钉死为 `windows-2022`（避免 `windows-latest` 静默升级），`resolve` job 用 `ubuntu-24.04`。

## 构建步骤

三 job 流水线：

1. **resolve**（ubuntu-24.04）：从 `push.tag` 或 `workflow_dispatch` 输入解析出 tag 与 ref，传出给下游。
2. **build**（windows-2022）：
   1. `actions/checkout@v4` 拉取 ref
   2. `astral-sh/setup-uv@v5` 安装 uv
   3. 校验 tag（去掉 `v` 前缀）与 `pyproject.toml` 的 `version` 字段一致，不一致则失败（除非传入 `skip_version_check`）
   4. `uv sync` 安装运行依赖（lite 配置，不含 transcribe extra）
   5. `uv run python scripts/build_exe.py --edition lite` 打包 Windows 文件夹版
   6. PowerShell `Compress-Archive` 将 `dist/BilibiliDownloaderUI` 压缩为 zip
   7. 解压 zip 校验内部存在 `BilibiliDownloaderUI/BilibiliDownloaderUI.exe`，结构异常则失败
   8. `actions/upload-artifact@v4` 把 zip 上传为 artifact
3. **publish**（windows-2022）：下载 artifact，`softprops/action-gh-release@v2` 将 zip 上传到 tag 对应的 Release，并自动生成 release notes

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
# 1. 同步版本号：更新 pyproject.toml 的 version 字段
# 2. 提交改动并推送到 main
git add .
git commit -m "chore: release v0.2.3"
git push

# 3. 打标签并推送（触发 CI）
git tag v0.2.3
git push origin v0.2.3

# 4. 查看 CI 进度
gh run list --workflow=Release
gh run watch

# 5. 失败时查看日志
gh run view <run-id> --log-failed

# 6. 用默认分支上最新 workflow + 现有 tag 重跑（不迁 tag 时）
gh workflow run Release -f tag=v0.2.3

# 7. 紧急重跑可跳过版本校验
gh workflow run Release -f tag=v0.2.3 -f skip_version_check=true
```

CI 成功后，Release 页面会自动出现 `v0.2.3` 及其 zip 附件。release notes 由 GitHub 根据 commits 自动生成，可后续在网页手动编辑。

## 注意事项

- **不要推 `v*` 前缀的非版本标签**，例如 `v-test`，会误触发 CI。临时标签用其他前缀（如 `dev-`）。
- lite 版**不包含转文字功能**。用户如需转文字，应按 README 使用 `uv sync --extra transcribe` 源码运行，或维护者本地打包 full 版。
- 打包脚本 `scripts/build_exe.py` 在打包完成后会校验 `_tcl_data` / `_tk_data` 等 Tkinter 运行数据是否存在，缺失则构建失败，避免发布启动即崩溃的 exe。
- Windows runner 默认控制台编码为 cp1252，`build_exe.py` 的中文 `print` 会触发 `UnicodeEncodeError`。工作流已通过 job 级别 `env: PYTHONUTF8: '1'` 启用 Python UTF-8 模式解决，修改源码时无需顾虑。
- `pyproject.toml` 中默认 index 为清华镜像，CI（境外 runner）也能访问；若 CI 因镜像不稳定失败，可在工作流中用 `UV_INDEX_URL` 环境变量覆盖为 `https://pypi.org/simple`。
- **版本一致性**：tag（去 `v` 前缀）必须与 `pyproject.toml` 的 `version` 字段一致，否则 build 阶段会失败。紧急重跑可传 `skip_version_check=true` 跳过。
- **Runner 钉版本**：工作流使用 `windows-2022` 与 `ubuntu-24.04`，避免 `*-latest` 镜像迁移带来的行为变化。升级 runner 时单独评估。
- full 版仍需本地手动发布，流程不变，见 [GitHubRelease发布说明.md](GitHubRelease发布说明.md)。

## 与现有发布方式的关系

| 场景 | 方式 | 文档 |
|---|---|---|
| lite 版（仅下载） | CI 自动发布 | 本文档 |
| full 版（含转文字） | 维护者本地打包手动上传 | GitHubRelease发布说明.md |
| 源码运行 | 用户 `uv sync` + `uv run bbdown-gui` | README.md |

三种方式互补，不冲突。
