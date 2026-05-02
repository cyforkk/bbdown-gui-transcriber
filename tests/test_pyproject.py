import sys
import tomllib
import unittest
from pathlib import Path


class PyprojectDependencyTests(unittest.TestCase):
    def setUp(self):
        self.pyproject = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))

    def test_default_dependencies_are_lightweight(self):
        dependencies = self.pyproject['project']['dependencies']

        self.assertEqual(dependencies, [])

    def test_transcribe_extra_contains_transcription_dependencies(self):
        dependencies = self.pyproject['project']['optional-dependencies']['transcribe']
        joined = '\n'.join(dependencies)

        self.assertIn('faster-whisper', joined)
        self.assertIn('nvidia-cublas-cu12', joined)
        self.assertIn('nvidia-cudnn-cu12', joined)


if __name__ == '__main__':
    unittest.main()
