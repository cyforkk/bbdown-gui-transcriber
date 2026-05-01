#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
ENTRY_FILE = PROJECT_DIR / 'src' / 'bbdown_gui' / 'app.py'
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'
APP_NAME = 'BilibiliDownloaderUI'


def build_pyinstaller_command() -> list[str]:
    return [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onedir',
        '--noconsole',
        '--clean',
        '--name',
        APP_NAME,
        '--collect-data',
        'faster_whisper',
        '--collect-binaries',
        'nvidia.cublas',
        '--collect-binaries',
        'nvidia.cudnn',
        '--distpath',
        str(DIST_DIR),
        '--workpath',
        str(BUILD_DIR),
        '--specpath',
        str(PROJECT_DIR),
        str(ENTRY_FILE),
    ]


def get_build_app_dir() -> Path:
    return DIST_DIR / APP_NAME


def get_build_exe_path() -> Path:
    return get_build_app_dir() / (APP_NAME + '.exe')


def main() -> int:
    if not ENTRY_FILE.exists():
        print('入口文件不存在：{0}'.format(ENTRY_FILE), file=sys.stderr)
        return 1

    command = build_pyinstaller_command()

    print('执行打包命令：')
    print(' '.join(command))
    completed = subprocess.run(command)
    if completed.returncode != 0:
        return completed.returncode

    app_dir = get_build_app_dir()
    exe_path = get_build_exe_path()
    if not exe_path.exists():
        print('打包命令已完成，但未找到 exe：{0}'.format(exe_path), file=sys.stderr)
        return 1

    print('打包完成：{0}'.format(app_dir))
    print('启动文件：{0}'.format(exe_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
