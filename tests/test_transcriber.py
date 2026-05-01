import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bbdown_gui import transcriber


class AudioTranscriberTests(unittest.TestCase):
    def test_is_supported_media_file_accepts_audio_and_video(self):
        self.assertTrue(transcriber.is_supported_media_file(Path('a.m4a')))
        self.assertTrue(transcriber.is_supported_media_file(Path('a.mp3')))
        self.assertTrue(transcriber.is_supported_media_file(Path('a.mp4')))

    def test_is_supported_media_file_rejects_text(self):
        self.assertFalse(transcriber.is_supported_media_file(Path('a.txt')))

    def test_get_transcript_path_uses_same_stem_txt(self):
        self.assertEqual(
            transcriber.get_transcript_path(Path('G:/默认收藏夹/音频/demo.m4a')),
            Path('G:/默认收藏夹/音频/demo.txt'),
        )

    def test_find_media_files_only_returns_supported_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            audio = folder / 'a.m4a'
            video = folder / 'b.mp4'
            text = folder / 'c.txt'
            audio.write_text('', encoding='utf-8')
            video.write_text('', encoding='utf-8')
            text.write_text('', encoding='utf-8')

            files = transcriber.find_media_files(folder)

        self.assertEqual(files, [audio, video])

    def test_find_cuda_dll_dirs_finds_cublas_and_cudnn(self):
        with tempfile.TemporaryDirectory() as tmp:
            site_packages = Path(tmp)
            cublas = site_packages / 'nvidia' / 'cublas' / 'bin'
            cudnn = site_packages / 'nvidia' / 'cudnn' / 'bin'
            cublas.mkdir(parents=True)
            cudnn.mkdir(parents=True)

            result = transcriber.find_cuda_dll_dirs([site_packages])

        self.assertEqual(result, (cublas, cudnn))

    def test_process_files_stops_before_next_file(self):
        calls = []
        stop = {'value': False}

        class FakeTranscriber:
            def transcribe_file(self, media_file):
                calls.append(media_file.name)
                stop['value'] = True
                return transcriber.TranscriptionResult(media_file, media_file.with_suffix('.txt'), True, None)

        files = [Path('a.m4a'), Path('b.m4a')]
        results = transcriber.process_media_files(files, FakeTranscriber(), should_stop=lambda: stop['value'])

        self.assertEqual(calls, ['a.m4a'])
        self.assertTrue(results.cancelled)
        self.assertEqual(len(results.items), 1)

    def test_probe_media_file_reports_invalid_file(self):
        with patch.object(transcriber.subprocess, 'run') as run:
            run.return_value.returncode = 1
            run.return_value.stdout = 'moov atom not found'

            ok, error = transcriber.probe_media_file(Path('bad.m4a'))

        self.assertFalse(ok)
        self.assertIn('moov atom not found', error)

    def test_transcribe_file_reports_empty_transcript(self):
        instance = object.__new__(transcriber.AudioTranscriber)
        instance.log = Mock()
        info = Mock(language='en', language_probability=0.5)
        instance.model = Mock()
        instance.model.transcribe.return_value = ([], info)

        with tempfile.TemporaryDirectory() as tmp:
            media_file = Path(tmp) / 'silent.m4a'
            media_file.write_bytes(b'fake')
            with patch.object(transcriber, 'probe_media_file', return_value=(True, None)):
                result = transcriber.AudioTranscriber.transcribe_file(instance, media_file)

        self.assertFalse(result.success)
        self.assertEqual(result.error, '未识别到可写入的文字内容')

    def test_probe_media_file_hides_ffprobe_window_on_windows(self):
        with patch.object(transcriber.sys, 'platform', 'win32'), patch.object(transcriber.subprocess, 'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = 'aac'

            transcriber.probe_media_file(Path('ok.m4a'))

        kwargs = run.call_args.kwargs
        self.assertIn('startupinfo', kwargs)
        self.assertTrue(kwargs['startupinfo'].dwFlags & transcriber.subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(kwargs['startupinfo'].wShowWindow, transcriber.subprocess.SW_HIDE)


if __name__ == '__main__':
    unittest.main()
