#!/usr/bin/env python3
import os
import site
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple


SUPPORTED_MEDIA_EXTENSIONS = ('.m4a', '.mp3', '.wav', '.flac', '.aac', '.mp4')


@dataclass(frozen=True)
class TranscriptionResult:
    input_path: Path
    output_path: Path
    success: bool
    error: Optional[str]


@dataclass(frozen=True)
class BatchTranscriptionResult:
    total: int
    items: List[TranscriptionResult]
    cancelled: bool = False


def is_supported_media_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS


def get_transcript_path(input_path: Path) -> Path:
    return input_path.with_suffix('.txt')


def find_media_files(folder_path: Path) -> List[Path]:
    return sorted(
        [path for path in folder_path.iterdir() if path.is_file() and is_supported_media_file(path)],
        key=lambda path: path.name.lower(),
    )


def probe_media_file(input_path: Path) -> Tuple[bool, Optional[str]]:
    try:
        completed = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', str(input_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    except FileNotFoundError:
        return True, None

    if completed.returncode != 0:
        return False, completed.stdout.strip() or '媒体文件无法被 ffprobe 解析'
    if not completed.stdout.strip():
        return False, '媒体文件中没有可识别的音频流'
    return True, None


def find_cuda_dll_dirs(search_paths: Sequence[Path]) -> Optional[Tuple[Path, Path]]:
    for path in search_paths:
        cublas_bin = path / 'nvidia' / 'cublas' / 'bin'
        cudnn_bin = path / 'nvidia' / 'cudnn' / 'bin'
        if cublas_bin.exists() and cudnn_bin.exists():
            return cublas_bin, cudnn_bin
    return None


def get_default_site_package_paths() -> List[Path]:
    paths = [Path.cwd() / '.venv' / 'Lib' / 'site-packages']
    paths.extend(Path(path) for path in site.getsitepackages())
    return paths


def load_cuda_dlls(search_paths: Optional[Sequence[Path]] = None) -> bool:
    if not hasattr(os, 'add_dll_directory'):
        return False

    paths = list(search_paths) if search_paths is not None else get_default_site_package_paths()
    dll_dirs = find_cuda_dll_dirs(paths)
    if not dll_dirs:
        return False

    cublas_bin, cudnn_bin = dll_dirs
    os.add_dll_directory(str(cublas_bin))
    os.add_dll_directory(str(cudnn_bin))
    os.environ['PATH'] = str(cublas_bin) + os.pathsep + str(cudnn_bin) + os.pathsep + os.environ.get('PATH', '')
    return True


class AudioTranscriber:
    def __init__(self, model_size: str = 'medium', device: str = 'cuda', compute_type: str = 'int8_float16', log: Callable[[str], None] = print):
        self.log = log
        load_cuda_dlls()
        self.log('正在加载 Faster-Whisper 模型：model={0}, device={1}, compute_type={2}\n'.format(model_size, device, compute_type))
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe_file(self, input_path: Path) -> TranscriptionResult:
        output_path = get_transcript_path(input_path)
        start_time = time.time()
        self.log('开始转文字：{0}\n'.format(input_path.name))

        valid, probe_error = probe_media_file(input_path)
        if not valid:
            error = '媒体文件无效：{0}'.format(probe_error)
            self.log('转文字失败：{0}，原因：{1}\n'.format(input_path, error))
            return TranscriptionResult(input_path, output_path, False, error)

        try:
            segments, info = self.model.transcribe(str(input_path), beam_size=5, vad_filter=True)
            self.log('语言检测：{0}，置信度：{1:.2f}\n'.format(info.language, info.language_probability))

            written = 0
            with output_path.open('w', encoding='utf-8') as output_file:
                for segment in segments:
                    text = segment.text.strip()
                    if not text:
                        continue
                    self.log('[{0:>7.2f}s] {1}\n'.format(segment.start, text))
                    output_file.write(text + '\n')
                    written += 1

            if written == 0:
                output_path.unlink(missing_ok=True)
                error = '未识别到可写入的文字内容'
                self.log('转文字失败：{0}，原因：{1}\n'.format(input_path, error))
                return TranscriptionResult(input_path, output_path, False, error)

            duration = time.time() - start_time
            self.log('转文字完成：{0}，耗时 {1:.2f} 秒\n'.format(output_path.name, duration))
            return TranscriptionResult(input_path, output_path, True, None)
        except Exception as exc:
            self.log('转文字失败：{0}，原因：{1}\n'.format(input_path, exc))
            return TranscriptionResult(input_path, output_path, False, str(exc))


def never_stop() -> bool:
    return False


def process_media_files(
    media_files: Iterable[Path],
    transcriber: AudioTranscriber,
    should_stop: Callable[[], bool] = never_stop,
) -> BatchTranscriptionResult:
    files = list(media_files)
    results = []
    cancelled = False

    for media_file in files:
        if should_stop():
            cancelled = True
            break
        results.append(transcriber.transcribe_file(media_file))
        if should_stop():
            cancelled = True
            break

    return BatchTranscriptionResult(total=len(files), items=results, cancelled=cancelled)
