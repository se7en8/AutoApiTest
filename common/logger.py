"""
日志配置模块
基于 loguru，默认从 config.py 的 LOG_CONFIG 读取配置，支持参数覆盖
"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
import setting as config


def setup_logger(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_to_console: Optional[bool] = None,
    log_to_file: Optional[bool] = None,
    max_file_size: Optional[int] = None,
    backup_count: Optional[int] = None,
):
    """配置 loguru 日志，未传参时从 config.LOG_CONFIG 读取"""
    cfg = config.LOG_CONFIG

    _log_level = log_level if log_level is not None else cfg['log_level']
    _log_dir = log_dir if log_dir is not None else cfg['log_dir']
    _log_to_console = log_to_console if log_to_console is not None else cfg['log_to_console']
    _log_to_file = log_to_file if log_to_file is not None else cfg['log_to_file']
    _max_file_size = max_file_size if max_file_size is not None else cfg['max_file_size']
    _backup_count = backup_count if backup_count is not None else cfg['backup_count']

    logger.remove()

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    if _log_to_console:
        logger.add(
            sys.stdout,
            format=fmt,
            level=_log_level,
            enqueue=True,
            colorize=True
        )

    if _log_to_file:
        log_path = Path(_log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / 'auto_api_test_{time:YYYYMMDD}.log'
        max_size_mb = _max_file_size // (1024 * 1024)

        logger.add(
            str(log_file),
            format=fmt,
            level=_log_level,
            rotation=f'{max_size_mb} MB',
            retention=_backup_count,
            encoding='utf-8',
            enqueue=True,
            colorize=False
        )

    return logger


logger = setup_logger()
