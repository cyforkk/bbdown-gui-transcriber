import locale
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bbdown_gui import app as ui_module


class BilibiliDownloaderUITests(unittest.TestCase):
    def test_get_subprocess_output_encoding_uses_locale_encoding(self):
        with patch.object(locale, 'getpreferredencoding', return_value='cp936'):
            self.assertEqual(ui_module.get_subprocess_output_encoding(), 'cp936')

    def test_get_subprocess_output_encoding_falls_back_to_utf8(self):
        with patch.object(locale, 'getpreferredencoding', return_value=''):
            self.assertEqual(ui_module.get_subprocess_output_encoding(), 'utf-8')

    def test_is_bbdown_usable_returns_true_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe_path = Path(tmp) / 'BBDown.exe'
            exe_path.write_bytes(b'fake')

            self.assertTrue(ui_module.is_bbdown_usable(str(exe_path)))

    def test_is_bbdown_usable_returns_false_when_file_missing(self):
        self.assertFalse(ui_module.is_bbdown_usable(r'C:\does\not\exist\BBDown.exe'))

    def test_get_hidden_subprocess_kwargs_hides_window_on_windows(self):
        with patch.object(ui_module.sys, 'platform', 'win32'):
            kwargs = ui_module.get_hidden_subprocess_kwargs()

        self.assertIn('startupinfo', kwargs)
        self.assertTrue(kwargs['startupinfo'].dwFlags & subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(kwargs['startupinfo'].wShowWindow, subprocess.SW_HIDE)

    def test_get_hidden_subprocess_kwargs_empty_off_windows(self):
        with patch.object(ui_module.sys, 'platform', 'linux'):
            self.assertEqual(ui_module.get_hidden_subprocess_kwargs(), {})

    def test_stop_task_marks_stop_and_terminates_current_process(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        process = Mock()
        process.poll.return_value = None
        instance.current_process = process
        instance.stop_requested = False
        instance.status = Mock()
        instance.stop_button = Mock()
        instance.log = Mock()

        ui_module.BilibiliDownloaderUI.stop_task(instance)

        self.assertTrue(instance.stop_requested)
        process.terminate.assert_called_once()
        instance.status.set.assert_called_with('正在停止...')

    def test_should_stop_returns_stop_requested(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.stop_requested = True

        self.assertTrue(ui_module.BilibiliDownloaderUI.should_stop(instance))

    def test_detect_bbdown_executable_uses_application_dir_when_cwd_and_user_dir_missing(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = False
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'LOCAL_BBDOWN')

    def test_detect_bbdown_executable_uses_path_when_local_missing(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True), patch.object(ui_module.Path, 'home') as home:
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = False
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'PATH_BBDOWN')

    def test_detect_bbdown_executable_skips_unusable_local_and_uses_path(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable') as usable:
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = False
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir
            usable.side_effect = lambda value: str(value) == 'PATH_BBDOWN'

            self.assertEqual(ui_module.detect_bbdown_executable(), 'PATH_BBDOWN')

    def test_detect_bbdown_executable_returns_bbdown_when_nothing_usable(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value=None), patch.object(ui_module, 'is_bbdown_usable', return_value=False):
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = False
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'bbdown')

    def test_detect_bbdown_executable_uses_dotnet_tools_when_local_and_path_missing(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.shutil, 'which', return_value=None), patch.object(ui_module, 'is_bbdown_usable', return_value=True), patch.object(ui_module.Path, 'home') as home:
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = True
            dotnet_bbdown = Mock()
            dotnet_bbdown.is_file.return_value = True
            dotnet_bbdown.name = 'bbdown.exe'
            dotnet_bbdown.__str__ = Mock(return_value='DOTNET_BBDOWN')
            home_dir.iterdir.return_value = iter([dotnet_bbdown])
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'DOTNET_BBDOWN')

    def test_detect_bbdown_executable_prefers_cwd_over_user_and_app_dirs(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            cwd_bbdown = Mock()
            cwd_bbdown.is_file.return_value = True
            cwd_bbdown.name = 'bbdown.exe'
            cwd_bbdown.__str__ = Mock(return_value='CWD_BBDOWN')
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = True
            cwd_dir.iterdir.return_value = iter([cwd_bbdown])
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = True
            home_bbdown = Mock()
            home_bbdown.is_file.return_value = True
            home_bbdown.name = 'BBDown.exe'
            home_dir.iterdir.return_value = iter([home_bbdown])
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'CWD_BBDOWN')

    def test_detect_bbdown_executable_user_dir_scan_is_case_insensitive(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value=None), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = True
            user_bbdown = Mock()
            user_bbdown.is_file.return_value = True
            user_bbdown.name = 'BBDown.exe'
            user_bbdown.__str__ = Mock(return_value='USER_BBDOWN')
            other_file = Mock()
            other_file.is_file.return_value = True
            other_file.name = 'unrelated.txt'
            home_dir.iterdir.return_value = iter([other_file, user_bbdown])
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'USER_BBDOWN')

    def test_detect_bbdown_executable_prefers_user_dir_over_application_dir(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.Path, 'cwd') as cwd, patch.object(ui_module.Path, 'home') as home, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            cwd_dir = Mock()
            cwd_dir.is_dir.return_value = False
            cwd.return_value = cwd_dir

            home_dir = Mock()
            home_dir.is_dir.return_value = True
            user_bbdown = Mock()
            user_bbdown.is_file.return_value = True
            user_bbdown.name = 'BBDown.exe'
            user_bbdown.__str__ = Mock(return_value='USER_BBDOWN')
            home_dir.iterdir.return_value = iter([user_bbdown])
            home_dir.__truediv__ = Mock(return_value=home_dir)
            home.return_value = home_dir

            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.is_file.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'USER_BBDOWN')

    def test_start_download_routes_favorite_and_collection_to_selection_flow(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.link = Mock()
        instance.link.get.return_value = 'https://space.bilibili.com/123/favlist?fid=456'
        instance.output_dir = Mock()
        instance.output_dir.get.return_value = 'OUTPUT_DIR'
        instance.bbdown_path = Mock()
        instance.bbdown_path.get.return_value = 'bbdown'
        instance.source_type = Mock()
        instance.source_type.get.return_value = 'collection'
        instance.mode = Mock()
        instance.mode.get.return_value = 'audio'
        instance.prepare_task = Mock(return_value=True)

        with patch.object(ui_module.messagebox, 'showwarning'), patch.object(ui_module.Path, 'mkdir'), patch.object(ui_module.threading, 'Thread') as thread_cls:
            ui_module.BilibiliDownloaderUI.start_download(instance)

        self.assertIs(thread_cls.call_args.kwargs['target'].__func__, ui_module.BilibiliDownloaderUI.run_fetch_and_select)

    def test_start_download_routes_single_video_to_direct_download(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.link = Mock()
        instance.link.get.return_value = 'BV1tkdVB4EpP'
        instance.output_dir = Mock()
        instance.output_dir.get.return_value = 'OUTPUT_DIR'
        instance.bbdown_path = Mock()
        instance.bbdown_path.get.return_value = 'bbdown'
        instance.source_type = Mock()
        instance.source_type.get.return_value = 'single'
        instance.mode = Mock()
        instance.mode.get.return_value = 'audio'
        instance.prepare_task = Mock(return_value=True)

        with patch.object(ui_module.messagebox, 'showwarning'), patch.object(ui_module.Path, 'mkdir'), patch.object(ui_module.threading, 'Thread') as thread_cls:
            ui_module.BilibiliDownloaderUI.start_download(instance)

        self.assertIs(thread_cls.call_args.kwargs['target'].__func__, ui_module.BilibiliDownloaderUI.run_download)

    def test_run_fetch_and_select_schedules_dialog_for_collection(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.stop_requested = False
        instance.root = Mock()

        videos = [ui_module.downloader.FavoriteVideo(bvid='BVcoll', title='c')]

        with patch.object(ui_module.downloader, 'parse_collection_id', return_value=('123', '456')), patch.object(ui_module.downloader, 'fetch_collection_videos', return_value=videos):
            ui_module.BilibiliDownloaderUI.run_fetch_and_select(instance, 'collection', 'https://example.com/lists/456?type=season', 'audio', 'OUT', 'bbdown')

        instance.root.after.assert_called_once()
        call_args = instance.root.after.call_args
        self.assertEqual(call_args.args[0], 0)
        self.assertEqual(call_args.args[1].__func__, ui_module.BilibiliDownloaderUI.handle_video_selection)
        self.assertEqual(call_args.args[2], videos)

    def test_run_fetch_and_select_schedules_dialog_for_favorite(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.stop_requested = False
        instance.root = Mock()

        videos = [ui_module.downloader.FavoriteVideo(bvid='BVfav', title='f')]

        with patch.object(ui_module.downloader, 'parse_media_id', return_value='456'), patch.object(ui_module.downloader, 'fetch_favorite_videos', return_value=videos):
            ui_module.BilibiliDownloaderUI.run_fetch_and_select(instance, 'favorite', 'https://example.com/favlist?fid=456', 'audio', 'OUT', 'bbdown')

        instance.root.after.assert_called_once()
        self.assertEqual(instance.root.after.call_args.args[2], videos)

    def test_run_fetch_and_select_empty_list_finishes_task(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.stop_requested = False
        instance.root = Mock()

        with patch.object(ui_module.downloader, 'parse_collection_id', return_value=('123', '456')), patch.object(ui_module.downloader, 'fetch_collection_videos', return_value=[]):
            ui_module.BilibiliDownloaderUI.run_fetch_and_select(instance, 'collection', 'https://example.com/lists/456?type=season', 'audio', 'OUT', 'bbdown')

        instance.output_queue.put.assert_called_once_with(('DONE', False))
        instance.root.after.assert_not_called()

    def test_handle_video_selection_starts_download_thread_with_selection(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.stop_requested = False
        instance.root = Mock()

        videos = [ui_module.downloader.FavoriteVideo(bvid='BV1', title='1'), ui_module.downloader.FavoriteVideo(bvid='BV2', title='2')]
        selection = [videos[0]]

        with patch.object(ui_module, 'open_video_selection_dialog', return_value=selection), patch.object(ui_module.threading, 'Thread') as thread_cls:
            ui_module.BilibiliDownloaderUI.handle_video_selection(instance, videos, 'audio', 'OUT', 'bbdown')

        thread_cls.assert_called_once()
        self.assertEqual(thread_cls.call_args.kwargs['target'].__func__, ui_module.BilibiliDownloaderUI.run_download_selected)
        self.assertEqual(thread_cls.call_args.kwargs['args'], (selection, 'audio', 'OUT', 'bbdown'))
        thread_cls.return_value.start.assert_called_once()
        instance.output_queue.put.assert_not_called()

    def test_handle_video_selection_cancel_finishes_task(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.stop_requested = False
        instance.root = Mock()

        videos = [ui_module.downloader.FavoriteVideo(bvid='BV1', title='1')]

        with patch.object(ui_module, 'open_video_selection_dialog', return_value=[]), patch.object(ui_module.threading, 'Thread') as thread_cls:
            ui_module.BilibiliDownloaderUI.handle_video_selection(instance, videos, 'audio', 'OUT', 'bbdown')

        thread_cls.assert_not_called()
        instance.output_queue.put.assert_called_once_with(('DONE', False))

    def test_run_download_selected_downloads_and_logs(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.log_download_result = Mock()
        instance.stop_requested = False
        instance.run_bbdown_command = Mock()

        videos = [ui_module.downloader.FavoriteVideo(bvid='BV1', title='1')]
        fake_result = ui_module.downloader.DownloadResult(total=1, successes=videos, failures=[], cancelled=False)

        with patch.object(ui_module.downloader, 'download_all', return_value=fake_result) as download_all:
            ui_module.BilibiliDownloaderUI.run_download_selected(instance, videos, 'audio', 'OUT', 'bbdown')

        download_all.assert_called_once()
        self.assertEqual(download_all.call_args.args[0], videos)
        instance.log_download_result.assert_called_once_with(fake_result)
        instance.output_queue.put.assert_called_with(('DONE', False))

    def test_run_download_collection_branch_fetches_and_downloads(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.log_download_result = Mock()
        instance.should_stop = Mock(return_value=False)
        instance.stop_requested = False
        instance.run_bbdown_command = Mock()

        fake_videos = [ui_module.downloader.FavoriteVideo(bvid='BVcoll', title='c')]
        fake_result = ui_module.downloader.DownloadResult(total=1, successes=fake_videos, failures=[], cancelled=False)

        with patch.object(ui_module.downloader, 'parse_collection_id', return_value=('3546743511714730', '7132285')), patch.object(ui_module.downloader, 'fetch_collection_videos', return_value=fake_videos), patch.object(ui_module.downloader, 'download_all', return_value=fake_result):
            ui_module.BilibiliDownloaderUI.run_download(instance, 'collection', 'https://space.bilibili.com/3546743511714730/lists/7132285?type=season', 'audio', r'G:\合集', 'bbdown')

        instance.log_download_result.assert_called_once_with(fake_result)

    def test_run_download_collection_branch_logs_empty_collection(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.log_download_result = Mock()
        instance.should_stop = Mock(return_value=False)
        instance.stop_requested = False
        instance.run_bbdown_command = Mock()

        with patch.object(ui_module.downloader, 'parse_collection_id', return_value=('3546743511714730', '7132285')), patch.object(ui_module.downloader, 'fetch_collection_videos', return_value=[]):
            ui_module.BilibiliDownloaderUI.run_download(instance, 'collection', 'https://space.bilibili.com/3546743511714730/lists/7132285?type=season', 'audio', r'G:\合集', 'bbdown')

        instance.log_download_result.assert_not_called()

    def test_run_transcription_uses_transcriber_module_without_shadowing(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.model_size = Mock()
        instance.model_size.get.return_value = 'medium'
        instance.device = Mock()
        instance.device.get.return_value = 'cuda'
        instance.compute_type = Mock()
        instance.compute_type.get.return_value = 'int8_float16'
        instance.stop_requested = False
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.log_transcription_result = Mock()
        instance.should_stop = Mock(return_value=False)

        fake_path = Mock()
        fake_path.is_dir.return_value = True
        fake_transcriber = Mock()
        fake_result = Mock()

        with patch.object(ui_module, 'Path', return_value=fake_path), patch.object(ui_module.transcriber, 'find_media_files', return_value=['a.m4a']), patch.object(ui_module.transcriber, 'AudioTranscriber', return_value=fake_transcriber), patch.object(ui_module.transcriber, 'process_media_files', return_value=fake_result):
            ui_module.BilibiliDownloaderUI.run_transcription(instance, 'G:/提取')

        instance.log_transcription_result.assert_called_once_with(fake_result)

    def test_run_transcription_logs_missing_optional_dependency_hint(self):
        instance = object.__new__(ui_module.BilibiliDownloaderUI)
        instance.model_size = Mock()
        instance.model_size.get.return_value = 'medium'
        instance.device = Mock()
        instance.device.get.return_value = 'cuda'
        instance.compute_type = Mock()
        instance.compute_type.get.return_value = 'int8_float16'
        instance.stop_requested = False
        instance.output_queue = Mock()
        instance.log = Mock()
        instance.should_stop = Mock(return_value=False)

        fake_path = Mock()
        fake_path.is_dir.return_value = False

        with patch.object(ui_module, 'Path', return_value=fake_path), patch.object(ui_module.transcriber, 'is_supported_media_file', return_value=True), patch.object(ui_module.transcriber, 'AudioTranscriber', side_effect=RuntimeError('当前未安装转文字依赖，请执行：uv sync --extra transcribe')):
            ui_module.BilibiliDownloaderUI.run_transcription(instance, 'G:/提取/a.m4a')

        instance.log.assert_any_call('当前未安装转文字依赖，请执行：uv sync --extra transcribe\n')


if __name__ == '__main__':
    unittest.main()
