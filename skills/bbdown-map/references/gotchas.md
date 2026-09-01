# 项目踩坑

本项目历史上踩过的坑，按场景组织。详细背景与修复见 `docs/问题总和文档.md` 对应条目，本文件只给定位口诀。

## 下载相关

| 场景 | 现象 | 第一检查点 | 详见 docs/问题总和文档.md 条目 |
| --- | --- | --- | --- |
| 合集下载报"获取视频合集失败" | 接口返回错误 | 确认用的是 `seasons_archives_list` 不是 `series/archives` | 视频合集下载报获取视频合集失败 |
| 合集接口裸请求被风控 | code=-352 或 HTML 错误页 | 确认走了 WBI 签名链路 | 同上 |
| 收藏夹/合集拉取数量不全 | 总数 1111 只拿 679 | 别用短页作终止条件，按 API 总数+bvid 去重 | 大合集拉取不全 |
| 拉到 1108/1111 差几个 | 差额是失效视频 | 接口不返回失效稿件，属预期 | 同上实测结论 |
| 收藏夹报"网络无法访问" | 实际是风控 | 间歇性 412，走 `read_json_with_retry` | B 站风控间歇性拦截 |
| BBDown 检测弹"未检测到" | 文件确实存在 | 别用 `--version` 子进程校验，改文件系统检查 | BBDown 自动检测漏掉用户目录 |
| 下载显示成功但目录空 | 假成功 | 必须扫新增文件且过滤全 0/过小/仅字幕 | BBDown 假成功问题 |

## GUI 相关

| 场景 | 现象 | 第一检查点 | 详见 docs/问题总和文档.md 条目 |
| --- | --- | --- | --- |
| 改了 GUI 代码没生效 | 行为没变 | 确认重启了 GUI 进程 | 经验教训（多处） |
| 弹窗列表空白无按钮 | Canvas 渲染失败 | 改用 Listbox，别用 Canvas+create_window | 视频选择弹窗 Canvas+Checkbutton 渲染空白 |
| 点确认报 invalid command name | 销毁后访问控件 | destroy 前把数据取出 | 弹窗确认时报 TclError |

## 打包相关

| 场景 | 现象 | 第一检查点 | 详见 docs/问题总和文档.md 条目 |
| --- | --- | --- | --- |
| exe 转文字报 silero_vad 缺失 | 模型文件没收集 | 加 `--collect-data faster_whisper` | exe 中 VAD 模型缺失 |
| exe 转文字报 cublas 缺失 | CUDA DLL 没收集 | 加 `--collect-binaries nvidia.cublas/cudnn` | release exe CUDA DLL 缺失 |
| 文件夹版 exe 启动报 _tcl_data 缺失 | 发布目录不完整 | build_exe 校验三个必要路径 | 文件夹版缺 Tcl/Tk 数据 |
| CI 中文输出 UnicodeEncodeError | cp1252 编码 | 设 `PYTHONUTF8=1` | GitHub Actions 中文输出报错 |

## 一个实用判断

- 下载/接口类问题 → 先看是否走了 `read_json_with_retry` 与 WBI 签名，再看分页终止条件。
- 检测类问题 → 先看是否还在用子进程做可用性探测。
- GUI 类问题 → 先确认跑的是新进程，再看是否用了不可靠的控件方案。
- 打包类问题 → 先看 `scripts/build_exe.py` 的 collect 参数是否齐全。
