"""
pytest 配置文件
定义 fixture 和测试配置
"""
import logging
import re
import pytest

from common.request_client import RequestClient
from common.variable_manager import VariableManager
from common.logger import logger
from common.allure_utils import write_environment_properties
import setting as cfg
from setting import reload_config, get_available_envs

# ── loguru → stdlib 桥接 ──────────────────────────────────────────
# Allure 通过 pytest 的 logging 插件捕获 stdlib logging 输出。
# 本项目使用 loguru，需将 loguru 消息桥接到 stdlib logging，
# 同时剥离 ANSI 转义序列，避免 Allure 报告中出现乱码。

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_BRIDGE_INSTALLED = False


def _loguru_to_stdlib_sink(msg: str) -> None:
    text = _ANSI_RE.sub('', msg).strip()
    if text:
        logging.getLogger('AutoApiTest').info(text)


def _install_loguru_bridge():
    global _BRIDGE_INSTALLED
    if _BRIDGE_INSTALLED:
        return
    logger.add(
        _loguru_to_stdlib_sink,
        format='{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}',
        level='DEBUG',
        colorize=False,
    )
    _BRIDGE_INSTALLED = True
    logging.getLogger('AutoApiTest').info('loguru → stdlib 桥接已安装')


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        '--environment',
        action='store',
        default=cfg.CURRENT_ENVIRONMENT,
        choices=list(get_available_envs().keys()),
        help=f'测试环境: {", ".join(get_available_envs().keys())}'
    )
    parser.addoption(
        '--stop-on-failure',
        action='store_true',
        default=cfg.RUN_CONFIG['stop_on_first_failure'],
        help='在第一次失败时停止测试'
    )


def pytest_configure(config):
    """pytest 配置"""
    environment = config.getoption('--environment')
    if environment:
        reload_config(environment)

    logger.info(f"配置已加载，当前环境: {cfg.CURRENT_ENVIRONMENT}, base_url: {cfg.BASE_URL}")

    _install_loguru_bridge()

    # markers 已在 pytest.ini 中定义，pytest 自动加载，无需在此重复注册


@pytest.fixture(scope='session')
def variable_manager() -> VariableManager:
    """变量管理器 fixture（会话级别，初始化时自动加载 config 中的全局变量）"""
    return VariableManager()


@pytest.fixture(scope='session')
def request_client(variable_manager: VariableManager) -> RequestClient:
    """请求客户端 fixture（会话级别）"""
    base_url = cfg.get_current_env_config()['base_url']
    logger.info(f"使用基础 URL: {base_url}")

    client = RequestClient(base_url=base_url, variable_manager=variable_manager)

    yield client
    client.close()


@pytest.fixture(scope='session')
def database():
    """数据库连接池 fixture（会话级别，通过 DATABASE_CONFIG['enabled'] 控制开关）"""
    cfg_db = cfg.DATABASE_CONFIG
    if not cfg_db.get('enabled', False):
        yield None
        return

    from common.database import DatabaseManager

    db = DatabaseManager()
    db.connect()
    yield db
    db.close()


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    logger.info(f"测试会话结束，退出状态: {exitstatus}")

    # 写入 Allure 环境信息（在会话结束时写入，确保环境正确）
    print()  # pytest 进度行末尾无换行，先补齐
    write_environment_properties()

    if not cfg.VARIABLE_CONFIG['persist_variables']:
        VariableManager.clear_variables()
        logger.info("全局变量已清理")
