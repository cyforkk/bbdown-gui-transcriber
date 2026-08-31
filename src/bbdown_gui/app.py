#!/usr/bin/env python3
import locale
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import List

from bbdown_gui import downloader
from bbdown_gui import transcriber




def get_application_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]



def is_bbdown_usable(executable: str) -> bool:
    path = Path(executable)
    if not path.is_file():
        return False
    if sys.platform == 'win32':
        return path.suffix.lower() == '.exe' or path.suffix == ''
    return os.access(path, os.X_OK)


def _is_bbdown_filename(name: str) -> bool:
    return name.lower() in ('bbdown.exe', 'bbdown')


def _find_bbdown_in_dir(directory: Path):
    if not directory.is_dir():
        return None
    for entry in directory.iterdir():
        if entry.is_file() and _is_bbdown_filename(entry.name):
            return entry
    return None


def detect_bbdown_executable() -> str:
    cwd_candidate = _find_bbdown_in_dir(Path.cwd())
    if cwd_candidate and is_bbdown_usable(str(cwd_candidate)):
        return str(cwd_candidate)

    dotnet_candidate = _find_bbdown_in_dir(Path.home() / '.dotnet' / 'tools')
    if dotnet_candidate and is_bbdown_usable(str(dotnet_candidate)):
        return str(dotnet_candidate)

    app_bbdown = get_application_dir() / 'bbdown.exe'
    if app_bbdown.is_file() and is_bbdown_usable(str(app_bbdown)):
        return str(app_bbdown)

    detected = shutil.which('bbdown')
    if detected and is_bbdown_usable(detected):
        return detected

    return 'bbdown'

def get_subprocess_output_encoding() -> str:
    return locale.getpreferredencoding(False) or 'utf-8'


def get_hidden_subprocess_kwargs() -> dict:
    if sys.platform != 'win32':
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {'startupinfo': startupinfo}


class QueueWriter:
    def __init__(self, output_queue: queue.Queue):
        self.output_queue = output_queue

    def write(self, text: str) -> None:
        if text:
            self.output_queue.put(text)

    def flush(self) -> None:
        pass


class BilibiliDownloaderUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('BBDown 哔哩哔哩下载器')
        self.root.geometry('920x760')

        self.output_queue = queue.Queue()
        self.source_type = tk.StringVar(value='favorite')
        self.mode = tk.StringVar(value='audio')
        self.link = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.home() / 'Downloads'))
        self.bbdown_path = tk.StringVar(value=detect_bbdown_executable())
        self.transcribe_path = tk.StringVar()
        self.model_size = tk.StringVar(value='medium')
        self.device = tk.StringVar(value='cuda')
        self.compute_type = tk.StringVar(value='int8_float16')
        self.status = tk.StringVar(value='就绪')
        self.is_running = False
        self.stop_requested = False
        self.current_process = None

        self.build_widgets()
        self.poll_output_queue()

    def build_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        download_frame = ttk.LabelFrame(main_frame, text='下载功能', padding=10)
        download_frame.pack(fill=tk.X)

        source_frame = ttk.Frame(download_frame)
        source_frame.pack(fill=tk.X)
        ttk.Label(source_frame, text='下载来源').pack(side=tk.LEFT)
        ttk.Radiobutton(source_frame, text='收藏夹链接', variable=self.source_type, value='favorite').pack(side=tk.LEFT, padx=(12, 0))
        ttk.Radiobutton(source_frame, text='单个视频链接 / BV号', variable=self.source_type, value='single').pack(side=tk.LEFT, padx=(20, 0))
        ttk.Radiobutton(source_frame, text='视频合集链接', variable=self.source_type, value='collection').pack(side=tk.LEFT, padx=(20, 0))

        link_frame = ttk.Frame(download_frame)
        link_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(link_frame, text='链接 / BV号').pack(anchor=tk.W)
        ttk.Entry(link_frame, textvariable=self.link).pack(fill=tk.X, pady=(4, 0))

        mode_frame = ttk.Frame(download_frame)
        mode_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(mode_frame, text='下载类型').pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text='音频', variable=self.mode, value='audio').pack(side=tk.LEFT, padx=(12, 0))
        ttk.Radiobutton(mode_frame, text='视频', variable=self.mode, value='video').pack(side=tk.LEFT, padx=(20, 0))

        output_frame = ttk.Frame(download_frame)
        output_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(output_frame, text='下载目录').pack(anchor=tk.W)
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Entry(output_row, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_row, text='选择目录', command=self.choose_output_dir).pack(side=tk.LEFT, padx=(8, 0))

        bbdown_frame = ttk.Frame(download_frame)
        bbdown_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(bbdown_frame, text='BBDown 可执行文件').pack(anchor=tk.W)
        bbdown_row = ttk.Frame(bbdown_frame)
        bbdown_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Entry(bbdown_row, textvariable=self.bbdown_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bbdown_row, text='选择 bbdown', command=self.choose_bbdown_path).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bbdown_row, text='自动检测', command=self.detect_bbdown).pack(side=tk.LEFT, padx=(8, 0))

        transcribe_frame = ttk.LabelFrame(main_frame, text='转文字功能', padding=10)
        transcribe_frame.pack(fill=tk.X, pady=(10, 0))

        transcribe_path_row = ttk.Frame(transcribe_frame)
        transcribe_path_row.pack(fill=tk.X)
        ttk.Entry(transcribe_path_row, textvariable=self.transcribe_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(transcribe_path_row, text='选择文件', command=self.choose_transcribe_file).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(transcribe_path_row, text='选择文件夹', command=self.choose_transcribe_folder).pack(side=tk.LEFT, padx=(8, 0))

        transcribe_options = ttk.Frame(transcribe_frame)
        transcribe_options.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(transcribe_options, text='模型').pack(side=tk.LEFT)
        ttk.Entry(transcribe_options, textvariable=self.model_size, width=12).pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(transcribe_options, text='设备').pack(side=tk.LEFT)
        ttk.Entry(transcribe_options, textvariable=self.device, width=10).pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(transcribe_options, text='计算类型').pack(side=tk.LEFT)
        ttk.Entry(transcribe_options, textvariable=self.compute_type, width=16).pack(side=tk.LEFT, padx=(6, 0))

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(12, 0))
        self.start_button = ttk.Button(action_frame, text='开始下载', command=self.start_download)
        self.start_button.pack(side=tk.LEFT)
        self.transcribe_button = ttk.Button(action_frame, text='开始转文字', command=self.start_transcription)
        self.transcribe_button.pack(side=tk.LEFT, padx=(8, 0))
        self.stop_button = ttk.Button(action_frame, text='停止任务', command=self.stop_task, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(action_frame, textvariable=self.status).pack(side=tk.LEFT, padx=(12, 0))

        log_frame = ttk.LabelFrame(main_frame, text='日志', padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title='选择下载目录')
        if selected:
            self.output_dir.set(selected)

    def choose_bbdown_path(self) -> None:
        selected = filedialog.askopenfilename(title='选择 BBDown 可执行文件')
        if selected:
            self.bbdown_path.set(selected)

    def choose_transcribe_file(self) -> None:
        selected = filedialog.askopenfilename(title='选择要转文字的音频/视频文件')
        if selected:
            self.transcribe_path.set(selected)

    def choose_transcribe_folder(self) -> None:
        selected = filedialog.askdirectory(title='选择要批量转文字的文件夹')
        if selected:
            self.transcribe_path.set(selected)

    def detect_bbdown(self) -> None:
        detected = detect_bbdown_executable()
        if detected != 'bbdown':
            self.bbdown_path.set(detected)
            messagebox.showinfo('检测成功', '已检测到 BBDown：\n{0}'.format(detected))
            return
        messagebox.showwarning('未检测到 BBDown', '未在 PATH 中检测到 bbdown，请手动选择 bbdown.exe。')

    def prepare_task(self, status_text: str) -> bool:
        if self.is_running:
            return False
        self.is_running = True
        self.stop_requested = False
        self.current_process = None
        self.start_button.configure(state=tk.DISABLED)
        self.transcribe_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status.set(status_text)
        self.append_log('========== 开始任务 ==========' + '\n')
        return True

    def start_download(self) -> None:
        source_text = self.link.get().strip()
        output_dir = self.output_dir.get().strip()
        bbdown_path = self.bbdown_path.get().strip() or 'bbdown'

        if not source_text:
            messagebox.showwarning('缺少链接', '请输入收藏夹链接、单个视频链接或 BV 号。')
            return
        if not output_dir:
            messagebox.showwarning('缺少下载目录', '请选择下载目录。')
            return
        if not self.prepare_task('下载中...'):
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        thread = threading.Thread(
            target=self.run_download,
            args=(self.source_type.get(), source_text, self.mode.get(), output_dir, bbdown_path),
            daemon=True,
        )
        thread.start()

    def start_transcription(self) -> None:
        target = self.transcribe_path.get().strip()
        if not target:
            messagebox.showwarning('缺少文件或文件夹', '请选择要转文字的文件或文件夹。')
            return
        if not Path(target).exists():
            messagebox.showwarning('路径不存在', '请选择存在的文件或文件夹。')
            return
        if not self.prepare_task('转文字中...'):
            return

        thread = threading.Thread(target=self.run_transcription, args=(target,), daemon=True)
        thread.start()

    def stop_task(self) -> None:
        if self.stop_requested:
            return

        self.stop_requested = True
        self.status.set('正在停止...')
        self.stop_button.configure(state=tk.DISABLED)
        self.log('用户请求停止任务\n')

        process = self.current_process
        if process and process.poll() is None:
            self.log('正在停止当前 BBDown 进程...\n')
            process.terminate()

    def should_stop(self) -> bool:
        return self.stop_requested

    def run_download(self, source_type: str, source_text: str, mode: str, output_dir: str, bbdown_path: str) -> None:
        try:
            self.log('下载类型: {0}\n'.format(mode))
            self.log('下载目录: {0}\n'.format(output_dir))
            self.log('BBDown: {0}\n'.format(bbdown_path))
            self.log('日志编码: {0}\n'.format(get_subprocess_output_encoding()))

            if source_type == 'single':
                bvid = downloader.parse_video_id(source_text)
                self.log('单个视频 BV: {0}\n'.format(bvid))
                result = downloader.download_single_video(source_text, mode, output_dir, bbdown_path=bbdown_path, runner=self.run_bbdown_command, should_stop=self.should_stop)
                self.log_download_result(result)
                return

            if source_type == 'collection':
                mid, season_id = downloader.parse_collection_id(source_text)
                self.log('视频合集 season_id: {0}\n'.format(season_id))
                self.log('正在获取视频合集列表...\n')
                videos = downloader.fetch_collection_videos(mid, season_id, source_text)
                if not videos:
                    self.log('视频合集为空，没有可下载的视频。\n')
                    return
                self.log('获取完成，共 {0} 个视频。\n'.format(len(videos)))
                result = downloader.download_all(videos, mode, output_dir, bbdown_path=bbdown_path, runner=self.run_bbdown_command, should_stop=self.should_stop)
                self.log_download_result(result)
                return

            media_id = downloader.parse_media_id(source_text)
            self.log('收藏夹 fid: {0}\n'.format(media_id))
            self.log('正在获取收藏夹视频列表...\n')
            videos = downloader.fetch_favorite_videos(media_id, source_text)
            if not videos:
                self.log('收藏夹为空，没有可下载的视频。\n')
                return
            self.log('获取完成，共 {0} 个视频。\n'.format(len(videos)))
            result = downloader.download_all(videos, mode, output_dir, bbdown_path=bbdown_path, runner=self.run_bbdown_command, should_stop=self.should_stop)
            self.log_download_result(result)
        except Exception as exc:
            self.log('任务失败：{0}\n'.format(exc))
        finally:
            self.output_queue.put(('DONE', self.stop_requested))

    def run_transcription(self, target: str) -> None:
        try:
            target_path = Path(target)
            if target_path.is_dir():
                files = transcriber.find_media_files(target_path)
            elif transcriber.is_supported_media_file(target_path):
                files = [target_path]
            else:
                self.log('不支持的文件类型：{0}\n'.format(target_path))
                return

            if not files:
                self.log('没有找到支持的音频/视频文件。\n')
                return

            audio_model = transcriber.AudioTranscriber(
                model_size=self.model_size.get().strip() or 'medium',
                device=self.device.get().strip() or 'cuda',
                compute_type=self.compute_type.get().strip() or 'int8_float16',
                log=self.log,
            )
            result = transcriber.process_media_files(files, audio_model, should_stop=self.should_stop)
            self.log_transcription_result(result)
        except RuntimeError as exc:
            message = str(exc)
            if message == transcriber.TRANSCRIBE_EXTRA_HINT:
                self.log(message + '\n')
            else:
                self.log('转文字任务失败：{0}\n'.format(exc))
        except Exception as exc:
            self.log('转文字任务失败：{0}\n'.format(exc))
        finally:
            self.output_queue.put(('DONE', self.stop_requested))

    def run_bbdown_command(self, command: List[str]) -> int:
        self.log('执行命令: {0}\n'.format(' '.join(command)))
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding=get_subprocess_output_encoding(),
            errors='replace',
            **get_hidden_subprocess_kwargs()
        )
        self.current_process = process

        if process.stdout:
            for line in process.stdout:
                self.log(line)
                if self.stop_requested and process.poll() is None:
                    process.terminate()

        return_code = process.wait()
        if self.current_process is process:
            self.current_process = None
        return return_code

    def log_download_result(self, result: downloader.DownloadResult) -> None:
        self.log('========== 下载统计 ==========' + '\n')
        self.log('总数：{0}\n'.format(result.total))
        self.log('成功：{0}\n'.format(len(result.successes)))
        self.log('失败：{0}\n'.format(len(result.failures)))
        if result.cancelled:
            self.log('状态：已停止\n')
        if result.failures:
            self.log('失败列表：\n')
            for failure in result.failures:
                self.log('- {0} {1}，原因：{2}\n'.format(failure.bvid, failure.title, failure.reason))

    def log_transcription_result(self, result: transcriber.BatchTranscriptionResult) -> None:
        successes = [item for item in result.items if item.success]
        failures = [item for item in result.items if not item.success]
        self.log('========== 转文字统计 ==========' + '\n')
        self.log('总数：{0}\n'.format(result.total))
        self.log('成功：{0}\n'.format(len(successes)))
        self.log('失败：{0}\n'.format(len(failures)))
        if result.cancelled:
            self.log('状态：已停止\n')
        for item in failures:
            self.log('- {0}，原因：{1}\n'.format(item.input_path.name, item.error))

    def log(self, text: str) -> None:
        self.output_queue.put(text)

    def append_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def poll_output_queue(self) -> None:
        while True:
            try:
                item = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if isinstance(item, tuple) and item[0] == 'DONE':
                stopped = bool(item[1])
                self.is_running = False
                self.current_process = None
                self.start_button.configure(state=tk.NORMAL)
                self.transcribe_button.configure(state=tk.NORMAL)
                self.stop_button.configure(state=tk.DISABLED)
                self.status.set('已停止' if stopped else '已完成')
                if stopped:
                    self.append_log('任务已停止\n')
                self.append_log('========== 任务结束 ==========' + '\n')
                continue

            self.append_log(str(item))

        self.root.after(100, self.poll_output_queue)


def main() -> None:
    root = tk.Tk()
    BilibiliDownloaderUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
