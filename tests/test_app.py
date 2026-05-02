import locale
import subprocess
import unittest
from unittest.mock import Mock, patch

from bbdown_gui import app as ui_module


class BilibiliDownloaderUITests(unittest.TestCase):
    def test_get_subprocess_output_encoding_uses_locale_encoding(self):
        with patch.object(locale, 'getpreferredencoding', return_value='cp936'):
            self.assertEqual(ui_module.get_subprocess_output_encoding(), 'cp936')

    def test_get_subprocess_output_encoding_falls_back_to_utf8(self):
        with patch.object(locale, 'getpreferredencoding', return_value=''):
            self.assertEqual(ui_module.get_subprocess_output_encoding(), 'utf-8')

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

    def test_detect_bbdown_executable_prefers_application_dir(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.exists.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'LOCAL_BBDOWN')

    def test_detect_bbdown_executable_uses_path_when_local_missing(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable', return_value=True):
            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.exists.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'PATH_BBDOWN')

    def test_detect_bbdown_executable_skips_unusable_local_and_uses_path(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.shutil, 'which', return_value='PATH_BBDOWN'), patch.object(ui_module, 'is_bbdown_usable') as usable:
            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.exists.return_value = True
            local_bbdown.__str__ = Mock(return_value='LOCAL_BBDOWN')
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir
            usable.side_effect = lambda value: str(value) == 'PATH_BBDOWN'

            self.assertEqual(ui_module.detect_bbdown_executable(), 'PATH_BBDOWN')

    def test_detect_bbdown_executable_returns_bbdown_when_nothing_usable(self):
        with patch.object(ui_module, 'get_application_dir') as app_dir, patch.object(ui_module.shutil, 'which', return_value=None), patch.object(ui_module, 'is_bbdown_usable', return_value=False):
            local_dir = Mock()
            local_bbdown = Mock()
            local_bbdown.exists.return_value = False
            local_dir.__truediv__ = Mock(return_value=local_bbdown)
            app_dir.return_value = local_dir

            self.assertEqual(ui_module.detect_bbdown_executable(), 'bbdown')

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
