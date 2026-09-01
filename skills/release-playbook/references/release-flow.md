# 发布流程

从"代码改完"到"GitHub Release 出现产物"的标准动作序列。前提：项目已配置 Release 工作流（`.github/workflows/release.yml`），推送 `v*` tag 即触发云端构建。

## 前置确认

- 已安装 `gh` 并 `gh auth login`，对仓库有写权限。
- 仓库 Actions 权限为 Read and write（否则上传 Release 报 `Resource not accessible by integration`）。
- 已知项目版本源在哪（见下表举例），知道如何读取与修改。

## 版本源（按项目技术栈，举例如下）

| 技术栈 | 版本源 | 读取方式 |
| --- | --- | --- |
| Python（uv/setuptools） | `pyproject.toml` 的 `version` 字段 | `grep '^version' pyproject.toml` |
| Node | `package.json` 的 `version` 字段 | `node -p "require('./package.json').version"` |
| Rust | `Cargo.toml` 的 `version` 字段 | `grep '^version' Cargo.toml` |
| Go | 根目录 `VERSION` 文件或 git tag 本身 | `cat VERSION` |
| 通用 | git tag 为唯一版本源 | `git describe --tags` |

tag 约定：`vX.Y.Z`，与版本源去 `v` 前缀后必须一致。

## 发布步骤

### 1. 同步版本号

打开版本源文件，把版本号改成新版本（如 `0.2.4`）。

### 2. 提交所有改动

```bash
git add -A
git commit -m "chore: release vX.Y.Z"
git push
```

若本次还有未提交的功能/修复改动，先按 `commit-guide.md` 拆分提交，最后单独发一个 `chore: release` 提交版本号变更。

### 3. 打 tag 并推送（触发 CI）

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

推送 tag 的瞬间，GitHub Actions 在云端 runner 上自动开始构建。

### 4. 查看 CI 进度

```bash
gh run list --workflow=Release
gh run watch
```

### 5. 失败排查

```bash
gh run view <run-id> --log-failed
```

常见失败：版本号不一致、构建脚本报错、产物校验不过、Actions 无写权限。

### 6. 用已有 tag 重跑（不迁 tag 时）

```bash
gh workflow run Release -f tag=vX.Y.Z
```

紧急跳过版本校验：

```bash
gh workflow run Release -f tag=vX.Y.Z -f skip_version_check=true
```

### 7. 验证发布

```bash
gh release view vX.Y.Z
```

应看到 Release 标题、release notes、产物附件。也可在仓库 Releases 页面查看。

## 手动发布（CI 不可用或需本地产物）

```bash
# 本地构建 + 压缩 + 用 gh 直接创建 Release
gh release create vX.Y.Z <产物文件路径> --title "项目名 vX.Y.Z" --generate-notes

# 已存在 tag，补传产物
gh release upload vX.Y.Z <产物文件路径> --clobber
```

`--generate-notes` 让 GitHub 按 commit 自动生成 release notes，可后续网页编辑。

## 一个实用判断

- CI 跑了但 Release 没产物 → 检查 build job 的产物路径与 upload 步骤是否对齐。
- CI 失败说"版本不一致" → 确认 tag 与版本源文件是否同步，不要硬跳校验。
- 推了 tag 没触发 CI → 确认 tag 是否匹配 `v*`、工作流文件是否在 `.github/workflows/`、仓库 Actions 是否启用。
