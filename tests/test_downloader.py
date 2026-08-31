import hashlib
import io
import tempfile
import unittest
import urllib.parse
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

    def test_parse_collection_id_from_collection_url(self):
        url = 'https://space.bilibili.com/3546743511714730/lists/7132285?type=season'

        mid, season_id = downloader.parse_collection_id(url)

        self.assertEqual(mid, '3546743511714730')
        self.assertEqual(season_id, '7132285')

    def test_parse_collection_id_rejects_url_without_lists_segment(self):
        with self.assertRaisesRegex(ValueError, '合集'):
            downloader.parse_collection_id('https://space.bilibili.com/3546743511714730/favlist?fid=123')

    def test_fetch_collection_videos_paginates_and_extracts_bvid(self):
        page_size = 30
        first_page = {'code': 0, 'data': {'archives': [
            {'bvid': 'BV{0}'.format(index), 'title': str(index)} for index in range(page_size)
        ]}}
        second_page = {'code': 0, 'data': {'archives': [
            {'bvid': 'BVlast', 'title': 'last'},
        ]}}

        calls = {'count': 0}

        def fake_read(url, referer):
            calls['count'] += 1
            return first_page if calls['count'] == 1 else second_page

        progress = []
        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', side_effect=fake_read):
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season', on_progress=progress.append)

        self.assertEqual(len(videos), page_size + 1)
        self.assertEqual(videos[0].bvid, 'BV0')
        self.assertEqual(videos[-1].bvid, 'BVlast')
        self.assertEqual(progress, [page_size, page_size + 1, page_size + 1])

    def test_fetch_collection_videos_continues_past_short_page_until_total(self):
        page_size = 30
        reported_total = 61
        short_page = {'code': 0, 'data': {'page': {'total': reported_total}, 'archives': [
            {'bvid': 'BV{0}'.format(index), 'title': str(index)} for index in range(19)
        ]}}
        tail_page = {'code': 0, 'data': {'page': {'total': reported_total}, 'archives': [
            {'bvid': 'BVtail', 'title': 'tail'},
        ]}}

        calls = {'count': 0}

        def fake_read(url, referer):
            calls['count'] += 1
            if calls['count'] == 1:
                return {'code': 0, 'data': {'page': {'total': reported_total}, 'archives': [
                    {'bvid': 'BVhead{0}'.format(index), 'title': str(index)} for index in range(page_size)
                ]}}
            if calls['count'] == 2:
                return short_page
            return tail_page

        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', side_effect=fake_read):
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season')

        self.assertEqual(len(videos), page_size + 19 + 1)
        self.assertEqual(calls['count'], 4)

    def test_fetch_collection_videos_warns_when_total_not_reachable(self):
        reported_total = 1111
        page = {'code': 0, 'data': {'page': {'total': reported_total}, 'archives': [
            {'bvid': 'BVonly', 'title': 'only'},
        ]}}

        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', return_value=page), patch('sys.stderr', new_callable=io.StringIO) as fake_err:
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season')

        self.assertEqual(len(videos), 1)
        self.assertIn('1111', fake_err.getvalue())
        self.assertIn('实际获取到 1 个', fake_err.getvalue())

    def test_fetch_collection_videos_warning_goes_to_callback_when_provided(self):
        reported_total = 1111
        page = {'code': 0, 'data': {'page': {'total': reported_total}, 'archives': [
            {'bvid': 'BVonly', 'title': 'only'},
        ]}}

        warnings = []
        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', return_value=page), patch('sys.stderr', new_callable=io.StringIO) as fake_err:
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season', on_warning=warnings.append)

        self.assertEqual(len(videos), 1)
        self.assertEqual(len(warnings), 1)
        self.assertIn('实际获取到 1 个', warnings[0])
        self.assertTrue(warnings[0].endswith('\n'))
        self.assertEqual(fake_err.getvalue(), '')

    def test_fetch_collection_videos_raises_clear_message_on_api_error(self):
        payload = {'code': -404, 'message': '合集不存在', 'data': None}

        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', return_value=payload):
            with self.assertRaisesRegex(RuntimeError, '合集不存在|私有'):
                downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season')

    def test_build_collection_api_url_uses_season_list_endpoint(self):
        url = downloader.build_collection_api_url('123', '456', 2, 30)

        parsed = urllib.parse.urlparse(url)
        self.assertEqual(parsed.netloc, 'api.bilibili.com')
        self.assertEqual(parsed.path, '/x/polymer/web-space/seasons_archives_list')
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(query['mid'], ['123'])
        self.assertEqual(query['season_id'], ['456'])
        self.assertEqual(query['page_num'], ['2'])
        self.assertEqual(query['page_size'], ['30'])
        self.assertEqual(query['sort_reverse'], ['false'])

    def test_build_collection_api_url_supports_legacy_endpoint(self):
        url = downloader.build_collection_api_url('123', '456', 1, 30, legacy=True)

        self.assertIn('x/polymer/space/seasons_archives_list', url)
        self.assertNotIn('web-space', url)

    def test_fetch_collection_videos_falls_back_to_legacy_endpoint(self):
        page = {'code': 0, 'data': {'archives': [{'bvid': 'BVok', 'title': 'ok'}]}}

        def fake_read(url, referer):
            if 'web-space' in url:
                raise OSError('blocked')
            return page

        with patch.object(downloader, 'get_wbi_mixin_key', return_value=None), patch.object(downloader, 'read_json_from_url', side_effect=fake_read):
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season')

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].bvid, 'BVok')

    def test_fetch_collection_videos_uses_signed_endpoint_when_available(self):
        page = {'code': 0, 'data': {'archives': [{'bvid': 'BVsigned', 'title': 'signed'}]}}

        def fake_read(url, referer):
            if 'w_rid' in url and 'web-space' in url:
                return page
            raise OSError('unexpected endpoint: {0}'.format(url))

        with patch.object(downloader, 'get_wbi_mixin_key', return_value='a' * 32), patch.object(downloader, 'read_json_from_url', side_effect=fake_read):
            videos = downloader.fetch_collection_videos('3546743511714730', '7132285', 'https://example.com/lists/7132285?type=season')

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].bvid, 'BVsigned')

    def test_sign_wbi_params_appends_wts_and_wrid(self):
        signed = downloader.sign_wbi_params({'mid': '123', 'season_id': '456'}, 'a' * 32)

        self.assertEqual(signed['mid'], '123')
        self.assertEqual(signed['season_id'], '456')
        self.assertTrue(signed['wts'].isdigit())
        self.assertEqual(len(signed['w_rid']), 32)

        expected_query = urllib.parse.urlencode(sorted({'mid': '123', 'season_id': '456', 'wts': signed['wts']}.items()))
        expected_rid = hashlib.md5((expected_query + 'a' * 32).encode('utf-8')).hexdigest()
        self.assertEqual(signed['w_rid'], expected_rid)

    def test_parser_accepts_collection_url_source(self):
        parser = downloader.create_parser()

        args = parser.parse_args([
            '--collection-url', 'https://space.bilibili.com/3546743511714730/lists/7132285?type=season',
            '--mode', 'audio',
            '--output-dir', r'G:\合集\音频',
        ])

        self.assertEqual(args.collection_url, 'https://space.bilibili.com/3546743511714730/lists/7132285?type=season')

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

    def test_fetch_favorite_videos_wraps_risk_control_error_with_friendly_hint(self):
        with patch.object(downloader, 'read_json_from_url', side_effect=RuntimeError('接口返回了拦截页而非数据（text/html），通常是哔哩哔哩风控的临时性拦截')), patch.object(downloader.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, '获取收藏夹失败'):
                downloader.fetch_favorite_videos('3928433616', 'https://example.com/favlist?fid=3928433616')

    def test_read_json_with_retry_retries_on_risk_control_then_succeeds(self):
        responses = [
            RuntimeError('请求被哔哩哔哩拒绝（HTTP 412），通常是站点风控的临时性拦截'),
            RuntimeError('接口返回了拦截页而非数据（text/html），通常是哔哩哔哩风控的临时性拦截'),
            {'code': 0, 'data': {}},
        ]
        calls = {'count': 0}

        def fake_read(url, referer):
            item = responses[calls['count']]
            calls['count'] += 1
            if isinstance(item, Exception):
                raise item
            return item

        with patch.object(downloader, 'read_json_from_url', side_effect=fake_read), patch.object(downloader.time, 'sleep') as fake_sleep:
            payload = downloader.read_json_with_retry('https://example.com/api', 'https://example.com/')

        self.assertEqual(payload, {'code': 0, 'data': {}})
        self.assertEqual(calls['count'], 3)
        self.assertEqual(fake_sleep.call_count, 2)

    def test_read_json_with_retry_does_not_retry_non_risk_errors(self):
        calls = {'count': 0}

        def fake_read(url, referer):
            calls['count'] += 1
            raise RuntimeError('请求超时')

        with patch.object(downloader, 'read_json_from_url', side_effect=fake_read), patch.object(downloader.time, 'sleep') as fake_sleep:
            with self.assertRaisesRegex(RuntimeError, '请求超时'):
                downloader.read_json_with_retry('https://example.com/api', 'https://example.com/')

        self.assertEqual(calls['count'], 1)
        fake_sleep.assert_not_called()

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
