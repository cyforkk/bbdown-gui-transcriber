#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Set


@dataclass(frozen=True)
class FavoriteVideo:
    bvid: str
    title: str


@dataclass(frozen=True)
class DownloadFailure:
    bvid: str
    title: str
    reason: str


@dataclass(frozen=True)
class DownloadResult:
    total: int
    successes: List[FavoriteVideo]
    failures: List[DownloadFailure]
    cancelled: bool = False


def parse_media_id(fav_url: str) -> str:
    parsed = urllib.parse.urlparse(fav_url)
    query = urllib.parse.parse_qs(parsed.query)
    fid_values = query.get('fid')
    if not fid_values or not fid_values[0].strip():
        raise ValueError('收藏夹链接中缺少 fid 参数，请检查链接是否正确。')
    return fid_values[0].strip()


def parse_video_id(video_url: str) -> str:
    text = video_url.strip()
    match = re.search(r'(BV[0-9A-Za-z]+)', text)
    if not match:
        raise ValueError('单个视频链接或 BV 号中没有找到 BV 号，请检查输入。')
    return match.group(1)


def read_json_from_url(url: str, referer: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': referer,
    }
    request = urllib.request.Request(url, headers=headers)

    content_type = ''
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            content_type = (response.headers.get('Content-Type') if response.headers else '') or ''
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            '请求被哔哩哔哩拒绝（HTTP {0}），通常是站点风控的临时性拦截，请稍等片刻再试。'.format(exc.code)
        ) from exc

    if 'json' not in content_type.lower():
        raise RuntimeError(
            '接口返回了拦截页而非数据（{0}），通常是哔哩哔哩风控的临时性拦截，请稍等片刻再试。'.format(content_type or 'Content-Type 缺失')
        )

    try:
        return json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError('接口响应异常，可能被哔哩哔哩风控临时拦截，请稍后重试。') from exc


def read_json_with_retry(url: str, referer: str, attempts: int = 3, on_retry=None) -> dict:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return read_json_from_url(url, referer)
        except RuntimeError as exc:
            last_error = exc
            message = str(exc)
            is_risk_control = ('HTTP 4' in message) or ('拦截' in message) or ('响应异常' in message)
            if not is_risk_control or attempt == attempts:
                raise
            if on_retry:
                on_retry(attempt, exc)
            time.sleep(2 * attempt)
    raise last_error


def build_favorite_api_url(media_id: str, page_number: int, page_size: int) -> str:
    query = urllib.parse.urlencode(
        {
            'media_id': media_id,
            'pn': page_number,
            'ps': page_size,
            'keyword': '',
            'order': 'mtime',
            'type': 0,
            'tid': 0,
            'platform': 'web',
        }
    )
    return 'https://api.bilibili.com/x/v3/fav/resource/list?{0}'.format(query)


def fetch_favorite_videos(media_id: str, referer: str, on_progress: Callable[[int], None] = None, on_warning: Callable[[str], None] = None) -> List[FavoriteVideo]:
    page_number = 1
    page_size = 20
    videos = []
    seen = set()
    reported_total = None

    while True:
        api_url = build_favorite_api_url(media_id, page_number, page_size)
        try:
            payload = read_json_with_retry(api_url, referer)
        except Exception as exc:
            raise RuntimeError('获取收藏夹失败：{0}。若稍后重试仍持续失败，可能是收藏夹为私有或不存在。'.format(exc)) from exc

        if payload.get('code') != 0:
            message = payload.get('message') or '未知错误'
            raise RuntimeError('获取收藏夹失败：{0}。可能是未登录、收藏夹为私有，或收藏夹不存在。'.format(message))

        data = payload.get('data') or {}
        medias = data.get('medias') or []
        if reported_total is None:
            reported_total = ((data.get('info') or {}).get('media_count'))

        new_count = 0
        for media in medias:
            bvid = str(media.get('bvid') or '').strip()
            if bvid and bvid not in seen:
                seen.add(bvid)
                videos.append(FavoriteVideo(bvid=bvid, title=str(media.get('title') or '')))
                new_count += 1

        if on_progress:
            on_progress(len(videos))

        if new_count == 0:
            break

        if reported_total is not None and len(videos) >= reported_total:
            break

        page_number += 1
        if page_number > 500:
            break

    if reported_total is not None and len(videos) < reported_total:
        warning = '警告：收藏夹共 {0} 个视频，实际获取到 {1} 个，其余可能是失效或受限视频。'.format(reported_total, len(videos))
        if on_warning:
            on_warning(warning + '\n')
        else:
            print(warning, file=sys.stderr)

    return videos


def parse_collection_id(collection_url: str) -> tuple[str, str]:
    path = urllib.parse.urlparse(collection_url.strip()).path
    match = re.search(r'/(\d+)/lists/(\d+)', path)
    if not match:
        raise ValueError('视频合集链接格式无法识别，期望形如 https://space.bilibili.com/<mid>/lists/<id>?type=season')
    return match.group(1), match.group(2)


SEASON_LIST_API_URL = 'https://api.bilibili.com/x/polymer/web-space/seasons_archives_list'
LEGACY_SEASON_LIST_API_URL = 'https://api.bilibili.com/x/polymer/space/seasons_archives_list'
WBI_NAV_API_URL = 'https://api.bilibili.com/x/web-interface/nav'
WBI_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

SEASON_SIGNED_ATTEMPT = (False, True)
SEASON_PLAIN_ATTEMPT = (False, False)
SEASON_LEGACY_ATTEMPT = (True, False)

_wbi_mixin_key_cache = None


def get_wbi_mixin_key():
    global _wbi_mixin_key_cache
    if _wbi_mixin_key_cache:
        return _wbi_mixin_key_cache

    try:
        payload = read_json_from_url(WBI_NAV_API_URL, 'https://www.bilibili.com/')
        wbi_img = ((payload.get('data') or {}).get('wbi_img') or {})
        img_key = str(wbi_img.get('img_url') or '').rsplit('/', 1)[-1].split('.')[0]
        sub_key = str(wbi_img.get('sub_url') or '').rsplit('/', 1)[-1].split('.')[0]
        raw_key = img_key + sub_key
    except Exception:
        return None

    if len(raw_key) < 64:
        return None

    _wbi_mixin_key_cache = ''.join(raw_key[index] for index in WBI_MIXIN_KEY_ENC_TAB)[:32]
    return _wbi_mixin_key_cache


def sign_wbi_params(params: dict, mixin_key: str) -> dict:
    signed = {str(key): str(value) for key, value in params.items()}
    signed['wts'] = str(int(time.time()))
    query = urllib.parse.urlencode(sorted(signed.items()))
    signed['w_rid'] = hashlib.md5((query + mixin_key).encode('utf-8')).hexdigest()
    return signed


def build_collection_api_url(mid: str, season_id: str, page_number: int, page_size: int, legacy: bool = False, signed: bool = False):
    params = {
        'mid': mid,
        'season_id': season_id,
        'sort_reverse': 'false',
        'page_num': page_number,
        'page_size': page_size,
    }

    if signed:
        mixin_key = get_wbi_mixin_key()
        if not mixin_key:
            return None
        params = sign_wbi_params(params, mixin_key)

    base_url = LEGACY_SEASON_LIST_API_URL if legacy else SEASON_LIST_API_URL
    return '{0}?{1}'.format(base_url, urllib.parse.urlencode(params))


def read_season_payload(mid: str, season_id: str, referer: str, page_number: int, page_size: int, preferred_attempt=None) -> tuple[dict, tuple]:
    attempts = [SEASON_SIGNED_ATTEMPT, SEASON_PLAIN_ATTEMPT, SEASON_LEGACY_ATTEMPT] if preferred_attempt is None else [preferred_attempt]
    last_error: Exception = RuntimeError('获取视频合集失败：可能是合集不存在、合集为私有，或网络无法访问哔哩哔哩。')

    for legacy, signed in attempts:
        api_url = build_collection_api_url(mid, season_id, page_number, page_size, legacy=legacy, signed=signed)
        if api_url is None:
            continue

        try:
            payload = read_json_with_retry(api_url, referer)
        except Exception as exc:
            last_error = exc
            continue

        if payload.get('code') == 0:
            return payload, (legacy, signed)

        last_error = RuntimeError('获取视频合集失败：{0}。可能是合集不存在或为私有。'.format(payload.get('message') or '未知错误'))

    raise RuntimeError('获取视频合集失败：可能是合集不存在、合集为私有，或网络无法访问哔哩哔哩。') from last_error


def fetch_collection_videos(mid: str, season_id: str, referer: str, on_progress: Callable[[int], None] = None, on_warning: Callable[[str], None] = None) -> List[FavoriteVideo]:
    page_number = 1
    page_size = 30
    videos = []
    seen = set()
    preferred_attempt = None
    reported_total = None

    while True:
        payload, preferred_attempt = read_season_payload(mid, season_id, referer, page_number, page_size, preferred_attempt)

        data = payload.get('data') or {}
        archives = data.get('archives') or []
        if reported_total is None:
            reported_total = (data.get('page') or {}).get('total')

        new_count = 0
        for archive in archives:
            bvid = str(archive.get('bvid') or '').strip()
            if bvid and bvid not in seen:
                seen.add(bvid)
                videos.append(FavoriteVideo(bvid=bvid, title=str(archive.get('title') or '')))
                new_count += 1

        if on_progress:
            on_progress(len(videos))

        if new_count == 0:
            break

        if reported_total is not None and len(videos) >= reported_total:
            break

        page_number += 1
        if page_number > 500:
            break

    if reported_total is not None and len(videos) < reported_total:
        warning = '警告：合集共 {0} 个视频，实际获取到 {1} 个，其余可能是失效或受限视频。'.format(reported_total, len(videos))
        if on_warning:
            on_warning(warning + '\n')
        else:
            print(warning, file=sys.stderr)

    return videos


def build_bbdown_command(bvid: str, mode: str, output_dir: str, bbdown_path: str = 'bbdown') -> List[str]:
    executable = bbdown_path.strip() if bbdown_path and bbdown_path.strip() else 'bbdown'
    if mode == 'audio':
        return [executable, bvid, '--audio-only', '--work-dir', output_dir]
    return [executable, bvid, '--work-dir', output_dir]


DOWNLOAD_OUTPUT_EXTENSIONS = {
    '.aac',
    '.ass',
    '.flac',
    '.m4a',
    '.m4s',
    '.mkv',
    '.mp3',
    '.mp4',
    '.srt',
    '.wav',
}
PRIMARY_MEDIA_EXTENSIONS = {
    '.aac',
    '.flac',
    '.m4a',
    '.m4s',
    '.mkv',
    '.mp3',
    '.mp4',
    '.wav',
}
MIN_DOWNLOAD_FILE_SIZE = 1024


def snapshot_download_outputs(output_dir: str) -> Set[Path]:
    root = Path(output_dir)
    if not root.exists():
        return set()
    return {path for path in root.rglob('*') if path.is_file() and path.suffix.lower() in DOWNLOAD_OUTPUT_EXTENSIONS}


def find_new_download_outputs(output_dir: str, before: Set[Path]) -> List[Path]:
    return sorted(snapshot_download_outputs(output_dir) - before, key=lambda path: str(path).lower())


def has_nonzero_header(path: Path) -> bool:
    with path.open('rb') as file:
        data = file.read(4096)
    return bool(data) and any(byte != 0 for byte in data)


def is_valid_download_output(path: Path) -> bool:
    if path.suffix.lower() not in PRIMARY_MEDIA_EXTENSIONS:
        return False
    try:
        if path.stat().st_size < MIN_DOWNLOAD_FILE_SIZE:
            return False
        return has_nonzero_header(path)
    except OSError:
        return False


def filter_valid_download_outputs(paths: Iterable[Path]) -> List[Path]:
    return [path for path in paths if is_valid_download_output(path)]


def run_command(command: List[str]) -> int:
    completed = subprocess.run(command)
    return completed.returncode


def never_stop() -> bool:
    return False


def download_all(
    videos: Iterable[FavoriteVideo],
    mode: str,
    output_dir: str,
    bbdown_path: str = 'bbdown',
    runner: Callable[[List[str]], int] = run_command,
    should_stop: Callable[[], bool] = never_stop,
) -> DownloadResult:
    video_list = list(videos)
    successes = []
    failures = []
    cancelled = False

    for index, video in enumerate(video_list, start=1):
        if should_stop():
            cancelled = True
            print('用户已停止任务，不再继续下载后续视频。')
            break

        print('[{0}/{1}] 开始下载：{2} {3}'.format(index, len(video_list), video.bvid, video.title))
        command = build_bbdown_command(video.bvid, mode, output_dir, bbdown_path)
        output_snapshot = snapshot_download_outputs(output_dir)

        try:
            exit_code = runner(command)
        except Exception as exc:
            if should_stop():
                cancelled = True
                print('任务已停止：{0}'.format(video.bvid))
                break
            failures.append(DownloadFailure(video.bvid, video.title, str(exc)))
            print('下载异常，已跳过：{0}，原因：{1}'.format(video.bvid, exc), file=sys.stderr)
            continue

        if should_stop():
            cancelled = True
            if exit_code != 0:
                print('任务已停止：{0}'.format(video.bvid))
                break

        if exit_code == 0:
            new_outputs = find_new_download_outputs(output_dir, output_snapshot)
            if not new_outputs:
                reason = 'BBDown 执行完成，但未检测到下载文件'
                failures.append(DownloadFailure(video.bvid, video.title, reason))
                print('下载失败：{0}，原因：{1}'.format(video.bvid, reason), file=sys.stderr)
                continue
            valid_outputs = filter_valid_download_outputs(new_outputs)
            if not valid_outputs:
                reason = 'BBDown 执行完成，但未检测到有效下载文件'
                failures.append(DownloadFailure(video.bvid, video.title, reason))
                print('下载失败：{0}，原因：{1}'.format(video.bvid, reason), file=sys.stderr)
                continue
            successes.append(video)
            print('下载成功：{0}，文件：{1}'.format(video.bvid, valid_outputs[0]))
            continue

        failures.append(DownloadFailure(video.bvid, video.title, 'BBDown exit code {0}'.format(exit_code)))
        print('下载失败，已跳过：{0}，退出码：{1}'.format(video.bvid, exit_code), file=sys.stderr)

    return DownloadResult(total=len(video_list), successes=successes, failures=failures, cancelled=cancelled)


def download_single_video(
    video_url: str,
    mode: str,
    output_dir: str,
    bbdown_path: str = 'bbdown',
    runner: Callable[[List[str]], int] = run_command,
    should_stop: Callable[[], bool] = never_stop,
) -> DownloadResult:
    bvid = parse_video_id(video_url)
    video = FavoriteVideo(bvid=bvid, title='单个视频')
    return download_all([video], mode, output_dir, bbdown_path, runner, should_stop)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='批量下载哔哩哔哩收藏夹，或下载单个哔哩哔哩视频。')
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--fav-url', help='哔哩哔哩收藏夹链接，必须包含 fid 参数。')
    source_group.add_argument('--video-url', help='单个哔哩哔哩视频链接或 BV 号。')
    source_group.add_argument('--collection-url', help='哔哩哔哩视频合集链接，形如 https://space.bilibili.com/<mid>/lists/<id>?type=season。')
    parser.add_argument('--mode', required=True, choices=['audio', 'video'], help='下载模式：audio 只下载音频，video 下载视频。')
    parser.add_argument('--output-dir', required=True, help='下载目录，Windows 请直接传 G:\\xxx，Linux/macOS 请传 /path/to/dir。')
    parser.add_argument('--bbdown-path', default='bbdown', help='BBDown 可执行文件路径，默认使用 PATH 中的 bbdown。')
    return parser


def parse_args() -> argparse.Namespace:
    return create_parser().parse_args()


def print_result(result: DownloadResult) -> None:
    print('========== 下载统计 ==========')
    print('总数：{0}'.format(result.total))
    print('成功：{0}'.format(len(result.successes)))
    print('失败：{0}'.format(len(result.failures)))
    if result.cancelled:
        print('状态：已停止')

    if result.failures:
        print('失败列表：')
        for failure in result.failures:
            print('- {0} {1}，原因：{2}'.format(failure.bvid, failure.title, failure.reason))


def main() -> int:
    args = parse_args()

    try:
        output_dir = str(Path(args.output_dir).expanduser())
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print('下载模式: {0}'.format(args.mode))
        print('下载目录: {0}'.format(output_dir))
        print('BBDown: {0}'.format(args.bbdown_path))

        if args.video_url:
            bvid = parse_video_id(args.video_url)
            print('单个视频 BV: {0}'.format(bvid))
            result = download_single_video(args.video_url, args.mode, output_dir, args.bbdown_path)
            print_result(result)
            return 0

        if args.collection_url:
            mid, season_id = parse_collection_id(args.collection_url)
            print('视频合集 season_id: {0}'.format(season_id))
            print('正在获取视频合集列表...')

            videos = fetch_collection_videos(mid, season_id, args.collection_url)
            if not videos:
                print('视频合集为空，没有可下载的视频。')
                return 0

            print('获取完成，共 {0} 个视频。'.format(len(videos)))
            result = download_all(videos, args.mode, output_dir, args.bbdown_path)
            print_result(result)
            return 0

        media_id = parse_media_id(args.fav_url)
        print('收藏夹 fid: {0}'.format(media_id))
        print('正在获取收藏夹视频列表...')

        videos = fetch_favorite_videos(media_id, args.fav_url)
        if not videos:
            print('收藏夹为空，没有可下载的视频。')
            return 0

        print('获取完成，共 {0} 个视频。'.format(len(videos)))
        result = download_all(videos, args.mode, output_dir, args.bbdown_path)
        print_result(result)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
