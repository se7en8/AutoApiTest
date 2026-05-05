"""
Allure 报告工具
环境信息写入、历史趋势、报告生成与打开
"""
import shutil
import subprocess
import sys
from pathlib import Path

import setting as config
from common.console import print_info, print_success, print_warn, print_error


def _get_allure_bin() -> str | None:
    """从系统 PATH 解析 allure 可执行文件"""
    from shutil import which

    allure_bin = config.ALLURE_CONFIG['allure_bin']
    path = which(allure_bin)
    if path is None:
        print_error(f'未在系统 PATH 中找到 allure 命令，请确认已安装并添加到环境变量')
        print_warn('安装参考: https://docs.qameta.io/allure-report/#_installing_a_commandline')
        return None
    return path


def write_environment_properties():
    """
    将环境信息写入 allure-results/environment.properties

    内容来源:
      - 动态: 当前环境名、BASE_URL、Python 版本
      - 静态: ALLURE_CONFIG['environment_properties']
    """
    ac = config.ALLURE_CONFIG
    results_dir = Path(ac['results_dir'])
    if not results_dir.exists():
        return

    props = {
        'Environment': config.CURRENT_ENVIRONMENT,
        'BaseURL': config.BASE_URL,
        'Python': sys.version.split()[0],
    }
    props.update(ac.get('environment_properties', {}))

    prop_file = results_dir / 'environment.properties'
    prop_file.write_text('\n'.join(f'{k}={v}' for k, v in props.items()), encoding='utf-8')
    print_success(f'环境信息已写入: {prop_file}')


# ==================== 历史趋势 ====================

def _restore_history():
    """
    将上一次的 history 复制到 allure-results/ 中，用于生成趋势图

    恢复来源（按优先级）:
      1. allure-report/history/  — 上次生成的报告（最快）
      2. allure-history/         — 持久化备份（报告被清理后仍可用）
    """
    ac = config.ALLURE_CONFIG
    results_dir = Path(ac['results_dir'])
    report_history = Path(ac['report_dir']) / 'history'
    backup_history = Path(ac['history_dir'])

    source = None
    if report_history.exists():
        source = report_history
    elif backup_history.exists():
        source = backup_history

    if source is None:
        return

    dest = results_dir / 'history'
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(str(source), str(dest))
    print_success(f'历史数据已恢复: {source} → {dest}')


def _persist_history():
    """将刚生成的 report/history/ 备份到 history_dir，供下次恢复使用"""
    ac = config.ALLURE_CONFIG
    report_history = Path(ac['report_dir']) / 'history'
    backup_history = Path(ac['history_dir'])

    if not report_history.exists():
        return

    if backup_history.exists():
        shutil.rmtree(backup_history)
    shutil.copytree(str(report_history), str(backup_history))
    print_success(f'历史数据已备份: {backup_history}')


# ==================== 报告生成 / 打开 ====================

def generate_allure_report():
    """生成 Allure 报告（环境信息 → 恢复历史 → allure generate → 备份历史）"""
    allure_bin = _get_allure_bin()
    if allure_bin is None:
        return

    write_environment_properties()
    _restore_history()

    ac = config.ALLURE_CONFIG
    results_dir = Path(ac['results_dir'])
    report_dir = Path(ac['report_dir'])

    if not results_dir.exists():
        print_error(f'结果目录不存在: {results_dir}')
        return

    cmd = [allure_bin, 'generate', str(results_dir), '-o', str(report_dir), '--clean']
    print_info(f'生成 Allure 报告 ：{" ".join(cmd)}')

    result = subprocess.run(cmd, cwd=config.BASE_DIR, check=False)
    if result.returncode == 0:
        _persist_history()
        print_success(f'报告已生成: {report_dir}')
        print_info(f'使用命令打开报告: allure open {report_dir}')
    else:
        print_error(f'生成报告失败: 退出码 {result.returncode}')


def open_allure_report():
    """打开 Allure 报告"""
    allure_bin = _get_allure_bin()
    if allure_bin is None:
        return

    report_dir = Path(config.ALLURE_CONFIG['report_dir'])

    if not report_dir.exists():
        print_error(f'报告目录不存在: {report_dir}')
        print_warn('请先生成报告: python run_tests.py --generate-report')
        return

    cmd = [allure_bin, 'open', str(report_dir)]
    print_info(f'打开 Allure 报告 ：{" ".join(cmd)}')
    subprocess.run(cmd, cwd=config.BASE_DIR)


def review_allure_report():
    """查看 Allure 报告"""
    allure_bin = _get_allure_bin()
    if allure_bin is None:
        return
    
    ac = config.ALLURE_CONFIG
    results_dir = Path(ac['results_dir'])
    cmd = [allure_bin, 'serve', str(results_dir)]
    print_info(f'预览 Allure 报告命令：{" ".join(cmd)}')
    try:
        subprocess.run(cmd, cwd=config.BASE_DIR, check=False)
    except KeyboardInterrupt:
        print_warn('预览已停止')
    except Exception:
        print_error('预览失败')
    
