"""
控制台输出模块
基于 rich 库，提供统一的格式化输出风格
"""
import os
import sys

# 确保 UTF-8 编码，rich 输出不受 GBK 限制
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

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


