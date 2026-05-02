#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
ENTRY_FILE = PROJECT_DIR / 'src' / 'bbdown_gui' / 'app.py'
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'
APP_NAME = 'BilibiliDownloaderUI'


def build_pyinstaller_command(edition: str = 'full') -> list[str]:
    command = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onedir',
        '--noconsole',
        '--clean',
        '--name',
        APP_NAME,
    ]
    if edition == 'full':
        command.extend([
            '--collect-data',
            'faster_whisper',
            '--collect-binaries',
            'nvidia.cublas',
            '--collect-binaries',
            'nvidia.cudnn',
        ])
    command.extend([
        '--distpath',
        str(DIST_DIR),
        '--workpath',
        str(BUILD_DIR),
        '--specpath',
        str(PROJECT_DIR),
        str(ENTRY_FILE),
    ])
    return command


def get_build_app_dir() -> Path:
    return DIST_DIR / APP_NAME


def get_build_exe_path() -> Path:
    return get_build_app_dir() / (APP_NAME + '.exe')


def get_required_build_paths(app_dir: Path) -> list[Path]:
    return [
        app_dir / (APP_NAME + '.exe'),
        app_dir / '_internal' / '_tcl_data',
        app_dir / '_internal' / '_tk_data',
    ]


def find_missing_required_build_paths(app_dir: Path) -> list[Path]:
    return [path for path in get_required_build_paths(app_dir) if not path.exists()]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='打包 BBDown GUI')
    parser.add_argument('--edition', choices=['lite', 'full'], default='full', help='lite 只包含下载功能；full 包含转文字依赖')
    return parser


def main() -> int:
    if not ENTRY_FILE.exists():
        print('入口文件不存在：{0}'.format(ENTRY_FILE), file=sys.stderr)
        return 1

    args = create_parser().parse_args()
    command = build_pyinstaller_command(args.edition)

    print('执行打包命令：')
    print(' '.join(command))
    completed = subprocess.run(command)
    if completed.returncode != 0:
        return completed.returncode

    app_dir = get_build_app_dir()
    exe_path = get_build_exe_path()
    missing_paths = find_missing_required_build_paths(app_dir)
    if missing_paths:
        print('打包命令已完成，但发布目录缺少必要文件：', file=sys.stderr)
        for missing_path in missing_paths:
            print('- {0}'.format(missing_path), file=sys.stderr)
        return 1

    print('打包完成：{0}'.format(app_dir))
    print('启动文件：{0}'.format(exe_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
