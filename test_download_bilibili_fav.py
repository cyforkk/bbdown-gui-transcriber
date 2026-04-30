import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name('download_bilibili_fav.py')
spec = importlib.util.spec_from_file_location('download_bilibili_fav', MODULE_PATH)
downloader = importlib.util.module_from_spec(spec)
sys.modules['download_bilibili_fav'] = downloader
spec.loader.exec_module(downloader)


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

        def fake_runner(command):
            return 1 if command[1] == 'BV_fail' else 0

        result = downloader.download_all(videos, 'audio', r'G:\默认收藏夹\音频', runner=fake_runner)

        self.assertEqual(result.total, 2)
        self.assertEqual(len(result.successes), 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].bvid, 'BV_fail')
        self.assertFalse(result.cancelled)

    def test_download_all_stops_before_next_video_when_cancelled(self):
        videos = [
            downloader.FavoriteVideo(bvid='BV_first', title='first'),
            downloader.FavoriteVideo(bvid='BV_second', title='second'),
        ]
        calls = []
        stop = {'value': False}

        def fake_runner(command):
            calls.append(command[1])
            stop['value'] = True
            return 0

        result = downloader.download_all(
            videos,
            'audio',
            r'G:\默认收藏夹\音频',
            runner=fake_runner,
            should_stop=lambda: stop['value'],
        )

        self.assertEqual(calls, ['BV_first'])
        self.assertEqual(len(result.successes), 1)
        self.assertTrue(result.cancelled)

    def test_download_single_video_uses_parsed_video_id(self):
        commands = []

        def fake_runner(command):
            commands.append(command)
            return 0

        result = downloader.download_single_video(
            'https://www.bilibili.com/video/BV1tkdVB4EpP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=xxx',
            'audio',
            r'G:\默认收藏夹\音频',
            runner=fake_runner,
        )

        self.assertEqual(result.total, 1)
        self.assertEqual(len(result.successes), 1)
        self.assertEqual(commands[0], ['bbdown', 'BV1tkdVB4EpP', '--audio-only', '--work-dir', r'G:\默认收藏夹\音频'])

    def test_download_single_video_uses_custom_bbdown_path(self):
        commands = []

        def fake_runner(command):
            commands.append(command)
            return 0

        downloader.download_single_video(
            'BV1tkdVB4EpP',
            'video',
            r'G:\默认收藏夹\视频',
            bbdown_path=r'C:\tools\bbdown.exe',
            runner=fake_runner,
        )

        self.assertEqual(commands[0], [r'C:\tools\bbdown.exe', 'BV1tkdVB4EpP', '--work-dir', r'G:\默认收藏夹\视频'])


if __name__ == '__main__':
    unittest.main()
