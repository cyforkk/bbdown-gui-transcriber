---
name: release-playbook
description: 当需求涉及"git 提交代码""写 commit message""打 tag 发布版本""触发 GitHub Release"时使用。命中关键字：提交、commit、push、tag、发布、release、版本号、gh、changelog。
---

# release-playbook

把"改完代码 → 中文提交 → 打 tag → 触发云端构建 → 验证发布"这条链路标准化。只管提交规范与发布动作序列，不绑定具体项目或构建工具。

## 使用顺序

- 提交代码前看 `references/commit-guide.md`，确认 commit message 格式与拆分粒度。
- 发布版本前看 `references/release-flow.md`，按版本源同步→提交→打 tag→推送→验证顺序执行。
- 收尾时看 `references/checklist.md`，逐条自检提交与发布质量。

## 必守约束

- commit message 用中文，遵循 `<类型>: <描述>` 格式，类型见 `references/commit-guide.md`。
- 一次提交只解决一类问题，不要把无关改动混在一起；大改动拆成多个 commit。
- 不要把构建产物、临时文件、IDE 配置提交进 git，依赖 `.gitignore` 排除。
- 发布前版本号必须同步：tag（去 `v` 前缀）与项目版本源（如 VERSION 文件 / pyproject.toml / package.json / Cargo.toml 等）完全一致，否则 CI 校验失败。
- tag 推送后等 CI 通过再宣告发布完成，不要在 CI 失败时强行补传产物掩盖问题。
- 紧急跳过版本校验只在发版阻塞时使用，事后必须补回版本同步。

## 参考资料

- `references/commit-guide.md`
- `references/release-flow.md`
- `references/checklist.md`
