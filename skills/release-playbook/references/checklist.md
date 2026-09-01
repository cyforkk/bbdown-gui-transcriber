# 提交与发布自检清单

每次提交或发布前逐条过一遍。

## 提交前

- [ ] `git status` 没有不该入库的文件（产物、临时、密钥、本地状态）。
- [ ] commit message 用中文，遵循 `<类型>: <描述>` 格式。
- [ ] 一次提交只解决一件事，无关改动已拆成独立 commit。
- [ ] message 正文说明了"为什么改"，不只是"改了什么"。
- [ ] 没有把大文件/二进制/构建产物混进提交。

## 发布前

- [ ] 版本源（VERSION / pyproject.toml / package.json / Cargo.toml 等）已改成新版本号。
- [ ] tag（去 `v` 前缀）与版本源完全一致。
- [ ] 所有待发布改动已提交并推送到默认分支。
- [ ] 工作树干净（`git status` 无未提交改动）。
- [ ] `gh auth status` 已登录且有写权限。
- [ ] 仓库 Actions 权限为 Read and write。

## 发布后

- [ ] tag 已推送，CI 已触发。
- [ ] `gh run watch` 看到 CI 通过（绿）。
- [ ] `gh release view vX.Y.Z` 看到产物附件。
- [ ] release notes 已生成（必要时手动编辑补充重要变更）。
- [ ] 失败时不要硬补传产物掩盖，先 `gh run view --log-failed` 排查根因。

## 每次都要问

- 这个 commit message 别人不看 diff 能看懂吗？
- 版本号真的同步了吗？
- CI 是真过了，还是我硬跳校验蒙混过去的？
- Release 产物用户能直接用吗（解压/双击/启动验证过吗）？
