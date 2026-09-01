# 对象词典

核心数据类。全部在 `src/bbdown_gui/` 下，`@dataclass(frozen=True)` 不可变。

## 下载相关（downloader.py）

| 对象 | 真相源 | 字段 | 作用 | 谁写 | 谁读 |
| --- | --- | --- | --- | --- | --- |
| `FavoriteVideo` | `downloader.py` | `bvid: str`、`title: str` | 列表里一个待下载视频 | `fetch_*_videos` 拉取时构造 | `download_all`、`open_video_selection_dialog` |
| `DownloadFailure` | `downloader.py` | `bvid: str`、`title: str`、`reason: str` | 一个下载失败项 | `download_all` 失败时构造 | `log_download_result` |
| `DownloadResult` | `downloader.py` | `total: int`、`successes: List[FavoriteVideo]`、`failures: List[DownloadFailure]`、`cancelled: bool=False` | 一次批量下载的汇总 | `download_all` 返回 | `log_download_result` |

## 转文字相关（transcriber.py）

| 对象 | 真相源 | 字段 | 作用 | 谁写 | 谁读 |
| --- | --- | --- | --- | --- | --- |
| `TranscriptionResult` | `transcriber.py` | `input_path: Path`、`output_path: Path`、`success: bool`、`error: Optional[str]` | 单个文件转写结果 | `process_media_files` 构造 | `log_transcription_result` |
| `BatchTranscriptionResult` | `transcriber.py` | `total: int`、`items: List[TranscriptionResult]`、`cancelled: bool=False` | 一次批量转写汇总 | `process_media_files` 返回 | `log_transcription_result` |

## 关键不变量

- 所有 dataclass 都 `frozen=True`，构造后不可改字段，要变更就新建实例。
- `bvid` 永远带 `BV` 前缀，由 `parse_video_id` 或 API 返回保证；不要在下游手动拼。
- `cancelled=True` 表示用户中途停止，此时 `successes` 可能非空（已完成的）。
- `DownloadResult.total` 是传入的 `video_list` 长度，不是 `len(successes)+len(failures)`（已停止时失败项可能不完整）。

## 常见误解

- 以为 `total == len(successes) + len(failures)`：停止场景下不等。
- 以为 `bvid` 不带前缀：实际带 `BV`。
- 以为拉取到的视频数等于 API 报告总数：失效/受限视频接口不返回，详见 `gotchas.md`。
