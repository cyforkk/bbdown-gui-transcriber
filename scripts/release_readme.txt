BBDown GUI 使用说明

1. 双击 BilibiliDownloaderUI\BilibiliDownloaderUI.exe 启动。
2. 当前是文件夹版发布，请保持 BilibiliDownloaderUI 文件夹内文件完整，不要只复制 exe。
3. 本程序不内置 BBDown。自动检测顺序：exe 同目录 bbdown.exe → 用户目录 .dotnet\tools\BBDown.exe → 系统 PATH → 手动选择。如需免配置，把 bbdown.exe 放到 BilibiliDownloaderUI.exe 同目录即可。
4. 支持收藏夹链接、视频合集链接、单个视频/BV号下载；收藏夹与合集下载前会弹出视频列表供选择（支持全选/全不选/反选/搜索过滤）。
5. 合集下载已内置 B 站 WBI 签名与风控自动重试，无需登录配置。
6. 转文字功能依赖 Faster-Whisper（仅 full 版含此依赖，lite 版无）；首次运行可能下载模型缓存，加载较慢。视频转文字识别音频流，不识别画面文字。
7. 大合集拉取不全时会有警告提示差额（失效/受限视频接口不返回）。

如打包后 exe 启动报 _tcl_data 缺失等错误，说明发布目录不完整，请重新打包。
