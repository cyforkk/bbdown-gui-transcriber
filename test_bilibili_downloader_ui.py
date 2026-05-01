import importlib.util
import locale
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

MODULE_PATH = Path(__file__).with_name('bilibili_downloader_ui.py')
spec = importlib.util.spec_from_file_location('bilibili_downloader_ui', MODULE_PATH)
ui_module = importlib.util.module_from_spec(spec)
sys.modules['bilibili_downloader_ui'] = ui_module
spec.loader.exec_module(ui_module)


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


if __name__ == '__main__':
    unittest.main()
