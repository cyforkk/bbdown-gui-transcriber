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


if __name__ == '__main__':
    unittest.main()
