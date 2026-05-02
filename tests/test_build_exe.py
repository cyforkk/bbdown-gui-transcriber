import unittest

from scripts import build_exe


class BuildExeTests(unittest.TestCase):
    def test_pyinstaller_command_collects_faster_whisper_data(self):
        command = build_exe.build_pyinstaller_command()

        self.assertIn('--collect-data', command)
        self.assertIn('faster_whisper', command)

    def test_pyinstaller_command_collects_cuda_binaries(self):
        command = build_exe.build_pyinstaller_command()

        self.assertIn('--collect-binaries', command)
        self.assertIn('nvidia.cublas', command)
        self.assertIn('nvidia.cudnn', command)

    def test_pyinstaller_command_builds_onedir_release(self):
        command = build_exe.build_pyinstaller_command()

        self.assertIn('--onedir', command)
        self.assertNotIn('--onefile', command)

    def test_build_exe_path_uses_onedir_output_folder(self):
        self.assertEqual(
            build_exe.get_build_exe_path(),
            build_exe.DIST_DIR / build_exe.APP_NAME / (build_exe.APP_NAME + '.exe'),
        )

    def test_required_build_paths_include_tkinter_runtime_data(self):
        paths = build_exe.get_required_build_paths(build_exe.DIST_DIR / build_exe.APP_NAME)

        self.assertIn(build_exe.DIST_DIR / build_exe.APP_NAME / 'BilibiliDownloaderUI.exe', paths)
        self.assertIn(build_exe.DIST_DIR / build_exe.APP_NAME / '_internal' / '_tcl_data', paths)
        self.assertIn(build_exe.DIST_DIR / build_exe.APP_NAME / '_internal' / '_tk_data', paths)

    def test_lite_pyinstaller_command_skips_transcription_dependencies(self):
        command = build_exe.build_pyinstaller_command('lite')

        self.assertNotIn('faster_whisper', command)
        self.assertNotIn('nvidia.cublas', command)
        self.assertNotIn('nvidia.cudnn', command)

    def test_full_pyinstaller_command_collects_transcription_dependencies(self):
        command = build_exe.build_pyinstaller_command('full')

        self.assertIn('faster_whisper', command)
        self.assertIn('nvidia.cublas', command)
        self.assertIn('nvidia.cudnn', command)


if __name__ == '__main__':
    unittest.main()
