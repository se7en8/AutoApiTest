"""
控制台输出模块
基于 rich 库，提供统一的格式化输出风格
统一处理 Windows 控制台 UTF-8 编码，确保 rich 和 loguru 输出不受 GBK 限制
"""
import os
import sys

# 环境变量：影响子进程和 Python 自身的编码行为
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

# 重配置 stdout/stderr 为 UTF-8（Python 3.7+），loguru 直接写 sys.stdout
for _stream_name in ('stdout', 'stderr'):
    _stream = getattr(sys, _stream_name)
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Windows 控制台代码页设为 UTF-8 (65001)
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes
        _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        _kernel32.SetConsoleOutputCP(65001)
        _STD_OUTPUT_HANDLE = -11
        _ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        _handle = _kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        _mode = wintypes.DWORD()
        if _kernel32.GetConsoleMode(_handle, ctypes.byref(_mode)):
            _mode.value |= _ENABLE_VIRTUAL_TERMINAL_PROCESSING
            _kernel32.SetConsoleMode(_handle, _mode)
    except Exception:
        pass

from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    'info': 'cyan',
    'success': 'bold green',
    'warn': 'bold yellow',
    'error': 'bold red',
    'label': 'bold cyan',
    'value': 'green',
    'path': 'dim cyan',
    'cmd': 'dim',
})

_console = Console(theme=_theme, force_terminal=True, legacy_windows=False)


def _print(*args, **kwargs):
    """安全输出，捕获编码异常"""
    try:
        _console.print(*args, **kwargs)
    except UnicodeEncodeError:
        text = ' '.join(str(a) for a in args)
        try:
            _console.print(text, **kwargs)
        except Exception:
            sys.stdout.write(text + '\n')


def print_info(msg: str):
    _print(f'[info][INFO] [/info] {msg}')


def print_success(msg: str):
    _print(f'[success][SUCCESS] [/success] {msg}')


def print_warn(msg: str):
    _print(f'[warn][WARN] [/warn] {msg}')


def print_error(msg: str):
    _print(f'[error][ERROR] [/error] {msg}')


def print_section(title: str):
    _print()
    _console.rule(f'[bold]{title}[/bold]')


