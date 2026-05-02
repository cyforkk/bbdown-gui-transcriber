import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bbdown_gui import downloader


def write_valid_media_file(path: Path) -> None:
    path.write_bytes(bytes([0, 0, 0, 24]) + b'ftypmp42' + (b'a' * 2048))


class DownloadBilibiliFavTests(unittest.TestCase):
    def test_parse_media_id_from_favorite_url(self):
        url = 'https://space.bilibili.com/619278616/favlist?fid=3928433616&ftype=create'

        media_id = downloader.parse_media_id(url)

        self.assertEqual(media_id, '3928433616')

    def test_parse_media_id_rejects_url_without_fid(self):
        url = 'https://space.bilibili.com/619278616/favlist?ftype=create'

        with self.assertRaisesRegex(ValueError, 'fid'):
            downloader.parse_media_id(url)

    def test_parse_video_id_from_video_url(self):
        url = 'https://www.bilibili.com/video/BV1tkdVB4EpP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=xxx'

        video_id = downloader.parse_video_id(url)

        self.assertEqual(video_id, 'BV1tkdVB4EpP')

    def test_parse_video_id_from_bv_id(self):
        video_id = downloader.parse_video_id('BV1tkdVB4EpP')

        self.assertEqual(video_id, 'BV1tkdVB4EpP')

    def test_parse_video_id_rejects_url_without_bv_id(self):
        with self.assertRaisesRegex(ValueError, 'BV'):
            downloader.parse_video_id('https://www.bilibili.com/')

    def test_parser_requires_favorite_or_single_video_source(self):
        parser = downloader.create_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(['--mode', 'audio', '--output-dir', r'G:\默认收藏夹\音频'])

    def test_parser_rejects_favorite_and_single_video_together(self):
        parser = downloader.create_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args([
                '--fav-url', 'https://space.bilibili.com/619278616/favlist?fid=3928433616&ftype=create',
                '--video-url', 'BV1tkdVB4EpP',
                '--mode', 'audio',
                '--output-dir', r'G:\默认收藏夹\音频',
            ])

    def test_build_bbdown_command_for_audio_keeps_output_dir_as_string(self):
        command = downloader.build_bbdown_command('BV1AkwyznE7G', 'audio', r'G:\默认收藏夹\音频')

        self.assertEqual(command, ['bbdown', 'BV1AkwyznE7G', '--audio-only', '--work-dir', r'G:\默认收藏夹\音频'])

    def test_build_bbdown_command_for_video(self):
        command = downloader.build_bbdown_command('BV1AkwyznE7G', 'video', '/home/me/videos')

        self.assertEqual(command, ['bbdown', 'BV1AkwyznE7G', '--work-dir', '/home/me/videos'])

    def test_build_bbdown_command_uses_custom_bbdown_path(self):
        command = downloader.build_bbdown_command('BV1AkwyznE7G', 'audio', r'G:\默认收藏夹\音频', r'C:\tools\bbdown.exe')

        self.assertEqual(command, [r'C:\tools\bbdown.exe', 'BV1AkwyznE7G', '--audio-only', '--work-dir', r'G:\默认收藏夹\音频'])

    def test_fetch_favorite_videos_raises_clear_message_when_api_rejects(self):
        payload = {'code': -403, 'message': '访问权限不足', 'data': None}

        with patch.object(downloader, 'read_json_from_url', return_value=payload):
            with self.assertRaisesRegex(RuntimeError, '未登录|私有|不存在'):
                downloader.fetch_favorite_videos('3928433616', 'https://example.com/favlist?fid=3928433616')

    def test_download_all_skips_failed_video(self):
        videos = [
            downloader.FavoriteVideo(bvid='BV_success', title='ok'),
            downloader.FavoriteVideo(bvid='BV_fail', title='bad'),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                if command[1] == 'BV_fail':
                    return 1
                write_valid_media_file(output_dir / 'success.m4a')
                return 0

            result = downloader.download_all(videos, 'audio', tmp, runner=fake_runner)

        self.assertEqual(result.total, 2)
        self.assertEqual(len(result.successes), 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].bvid, 'BV_fail')
        self.assertFalse(result.cancelled)

    def test_download_all_reports_failure_when_no_output_file_created(self):
        videos = [downloader.FavoriteVideo(bvid='BV_empty', title='empty')]

        with tempfile.TemporaryDirectory() as tmp:
            result = downloader.download_all(videos, 'audio', tmp, runner=lambda command: 0)

        self.assertEqual(len(result.successes), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('未检测到下载文件', result.failures[0].reason)

    def test_download_all_rejects_zero_filled_output_file(self):
        videos = [downloader.FavoriteVideo(bvid='BV_zero', title='zero')]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                (output_dir / 'zero.mp4').write_bytes(bytes([0]) * 4096)
                return 0

            result = downloader.download_all(videos, 'video', tmp, runner=fake_runner)

        self.assertEqual(len(result.successes), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('未检测到有效下载文件', result.failures[0].reason)

    def test_download_all_rejects_tiny_output_file(self):
        videos = [downloader.FavoriteVideo(bvid='BV_tiny', title='tiny')]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                (output_dir / 'tiny.mp4').write_bytes(b'ftyp')
                return 0

            result = downloader.download_all(videos, 'video', tmp, runner=fake_runner)

        self.assertEqual(len(result.successes), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('未检测到有效下载文件', result.failures[0].reason)

    def test_download_all_rejects_subtitle_only_output(self):
        videos = [downloader.FavoriteVideo(bvid='BV_subtitle', title='subtitle')]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                (output_dir / 'subtitle.srt').write_text('1' + chr(10) + 'hello', encoding='utf-8')
                return 0

            result = downloader.download_all(videos, 'video', tmp, runner=fake_runner)

        self.assertEqual(len(result.successes), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('未检测到有效下载文件', result.failures[0].reason)

    def test_download_all_accepts_success_when_output_file_created(self):
        videos = [downloader.FavoriteVideo(bvid='BV_success', title='ok')]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                write_valid_media_file(output_dir / 'ok.m4a')
                return 0

            result = downloader.download_all(videos, 'audio', tmp, runner=fake_runner)

        self.assertEqual(len(result.successes), 1)
        self.assertEqual(len(result.failures), 0)

    def test_download_all_stops_before_next_video_when_cancelled(self):
        videos = [
            downloader.FavoriteVideo(bvid='BV_first', title='first'),
            downloader.FavoriteVideo(bvid='BV_second', title='second'),
        ]
        calls = []
        stop = {'value': False}

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                calls.append(command[1])
                write_valid_media_file(output_dir / 'first.m4a')
                stop['value'] = True
                return 0

            result = downloader.download_all(
                videos,
                'audio',
                tmp,
                runner=fake_runner,
                should_stop=lambda: stop['value'],
            )

        self.assertEqual(calls, ['BV_first'])
        self.assertEqual(len(result.successes), 1)
        self.assertTrue(result.cancelled)

    def test_download_single_video_uses_parsed_video_id(self):
        commands = []

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                commands.append(command)
                write_valid_media_file(output_dir / 'single.m4a')
                return 0

            result = downloader.download_single_video(
                'https://www.bilibili.com/video/BV1tkdVB4EpP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=xxx',
                'audio',
                tmp,
                runner=fake_runner,
            )

        self.assertEqual(result.total, 1)
        self.assertEqual(len(result.successes), 1)
        self.assertEqual(commands[0], ['bbdown', 'BV1tkdVB4EpP', '--audio-only', '--work-dir', tmp])

    def test_download_single_video_uses_custom_bbdown_path(self):
        commands = []

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            def fake_runner(command):
                commands.append(command)
                write_valid_media_file(output_dir / 'custom.mp4')
                return 0

            downloader.download_single_video(
                'BV1tkdVB4EpP',
                'video',
                tmp,
                bbdown_path=r'C:	oolsbdown.exe',
                runner=fake_runner,
            )

        self.assertEqual(commands[0], [r'C:	oolsbdown.exe', 'BV1tkdVB4EpP', '--work-dir', tmp])


if __name__ == '__main__':
    unittest.main()
