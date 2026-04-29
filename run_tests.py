"""
测试执行入口
用于运行 API 自动化测试
"""
import sys
import os
import io
import setting as config
from setting import reload_config, get_available_envs
from common.runner import build_pytest_command, run_pytest
from common.allure_utils import generate_allure_report, open_allure_report, review_allure_report
from common.console import print_section, print_info


# ==================== 编码修复 ====================

def fix_console_encoding():
    """修复控制台编码问题，确保支持UTF-8输出"""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.SetConsoleOutputCP(65001)
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = wintypes.DWORD()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, mode)
        except Exception:
            try:
                os.system('chcp 65001 >nul 2>&1')
            except Exception:
                pass

    for stream_name in ['stdout', 'stderr']:
        stream = getattr(sys, stream_name)
        try:
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')
            elif hasattr(stream, 'buffer'):
                new_stream = io.TextIOWrapper(
                    stream.buffer, encoding='utf-8', errors='replace', write_through=True
                )
                setattr(sys, stream_name, new_stream)
        except Exception:
            try:
                if hasattr(stream, 'errors'):
                    stream.errors = 'replace'
            except Exception:
                pass


fix_console_encoding()


# ==================== CLI 入口 ====================

def main():
    import argparse

    env_names = list(get_available_envs().keys())

    parser = argparse.ArgumentParser(description='API 自动化测试执行脚本')
    parser.add_argument('--generate-report', action='store_true', help='生成 Allure 报告（不运行测试）')
    parser.add_argument('--open-report', action='store_true', help='打开 Allure 报告')
    parser.add_argument('--review-report', action='store_true', help='预览 Allure 报告')
    parser.add_argument('--run-and-report', action='store_true', help='运行测试并生成报告')
    parser.add_argument('--environment', type=str, choices=env_names,
        help=f'测试环境: {", ".join(env_names)}'
    )
    parser.add_argument('--stop-on-failure', action='store_true', help='在第一次失败时停止测试')
    parser.add_argument('--html-report', action='store_true', help='生成 HTML 报告')
    parser.add_argument(
        '--workers', type=int, default=config.RUN_CONFIG['workers'],
        help='并行工作进程数（0=自动，1=串行）'
    )

    args, remaining = parser.parse_known_args()

    # 根据 CLI 参数确定环境
    if args.environment:
        reload_config(args.environment)

    print_section('AutoApiTest')
    print_info(f'环境: {config.CURRENT_ENVIRONMENT.upper()}')
    print_info(f'基础 URL: {config.BASE_URL}')
    print_info(f'日志级别: {config.LOG_CONFIG["log_level"]}')

    if args.generate_report:
        generate_allure_report()
        return 0

    if args.open_report:
        open_allure_report()
        return 0
        
    if args.review_report:
        review_allure_report()
        return 0

    cmd = build_pytest_command(args)
    cmd.extend(remaining)

    returncode = run_pytest(cmd)

    if args.run_and_report and returncode in (0, 1):
        generate_allure_report()

    return returncode


if __name__ == '__main__':
    sys.exit(main())
