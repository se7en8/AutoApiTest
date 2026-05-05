"""
测试运行器
pytest 命令构建与执行
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import setting as config
from common.console import print_info, print_warn, print_error


def build_pytest_command(
    environment: Optional[str] = None,
    workers: int = 1,
    stop_on_failure: bool = False,
    html_report: bool = False,
) -> List[str]:
    """根据 ALLURE_CONFIG 和参数构建 pytest 命令列表"""
    allure_cfg = config.ALLURE_CONFIG

    cmd = [sys.executable, '-m', 'pytest']

    if allure_cfg.get('enabled', True):
        cmd.append(f'--alluredir={allure_cfg["results_dir"]}')
        if allure_cfg.get('clean_results', True):
            cmd.append('--clean-alluredir')

    if environment:
        cmd.append(f'--environment={environment}')
    if stop_on_failure:
        cmd.append('--stop-on-failure')
    if workers > 1:
        cmd.append(f'-n={workers}')
    if html_report:
        html_dir = Path(config.HTML_REPORT_DIR)
        html_dir.mkdir(parents=True, exist_ok=True)
        html_file = html_dir / 'report.html'
        cmd.append(f'--html={html_file}')
        cmd.append('--self-contained-html')

    return cmd


def run_pytest(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """执行 pytest 子进程并返回退出码"""
    if cwd is None:
        cwd = config.BASE_DIR

    print_info(f'运行命令：{" ".join(cmd)}')
    print_info(f'工作目录: {cwd}')

    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print_warn('测试被用户中断')
        return 1
    except Exception as e:
        print_error(f'运行测试时发生错误: {e}')
        return 1
