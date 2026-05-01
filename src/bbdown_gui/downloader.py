#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
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
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': referer,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


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


def fetch_favorite_videos(media_id: str, referer: str) -> List[FavoriteVideo]:
    page_number = 1
    page_size = 20
    videos = []

    while True:
        api_url = build_favorite_api_url(media_id, page_number, page_size)
        try:
            payload = read_json_from_url(api_url, referer)
        except Exception as exc:
            raise RuntimeError('获取收藏夹失败：可能是未登录、收藏夹为私有、收藏夹不存在，或网络无法访问哔哩哔哩。') from exc

        if payload.get('code') != 0:
            message = payload.get('message') or '未知错误'
            raise RuntimeError('获取收藏夹失败：{0}。可能是未登录、收藏夹为私有，或收藏夹不存在。'.format(message))

        data = payload.get('data') or {}
        medias = data.get('medias') or []
        for media in medias:
            bvid = str(media.get('bvid') or '').strip()
            if bvid:
                videos.append(FavoriteVideo(bvid=bvid, title=str(media.get('title') or '')))

        if len(medias) < page_size:
            return videos

        page_number += 1


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


def snapshot_download_outputs(output_dir: str) -> Set[Path]:
    root = Path(output_dir)
    if not root.exists():
        return set()
    return {path for path in root.rglob('*') if path.is_file() and path.suffix.lower() in DOWNLOAD_OUTPUT_EXTENSIONS}


def find_new_download_outputs(output_dir: str, before: Set[Path]) -> List[Path]:
    return sorted(snapshot_download_outputs(output_dir) - before, key=lambda path: str(path).lower())


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
            successes.append(video)
            print('下载成功：{0}，文件：{1}'.format(video.bvid, new_outputs[0]))
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
