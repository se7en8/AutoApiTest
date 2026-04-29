"""
基础配置类
所有环境配置的公共父类，定义全部默认值

子类必须重写:
  - CURRENT_ENVIRONMENT: 当前环境名称
  - BASE_URL: 环境对应的 API 基础地址

子类可选重写（按需覆盖）:
  - HTTP_CONFIG: 如 verify_ssl、timeout 等
  - LOG_CONFIG: 如 log_level
  - ALLURE_CONFIG: 如 enabled
  - RUN_CONFIG: 如 workers、stop_on_first_failure
"""
from pathlib import Path
from typing import Dict, Any


PROJECT_ROOT = Path(__file__).parent.parent


class BaseConfig:
    # ==================== 项目路径 ====================
    BASE_DIR: Path = PROJECT_ROOT

    # ===== 子类必须重写以下属性 =====
    CURRENT_ENVIRONMENT: str = 'dev'
    BASE_URL: str = 'http://dev.api.example.com'
    DESCRIPTION: str = ''  # 环境描述，用于 CLI 帮助信息

    # ==================== 日志 ====================
    LOG_CONFIG: Dict[str, Any] = {
        'log_level': 'INFO',
        'log_dir': str(PROJECT_ROOT / 'logs'),
        'log_to_console': True,
        'log_to_file': True,
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
    }

    # ==================== HTTP 请求 ====================
    HTTP_CONFIG: Dict[str, Any] = {
        'timeout': 30,
        'verify_ssl': True,
        'allow_redirects': True,
        'max_retries': 3,
        'retry_backoff_factor': 1,
        'retry_status_codes': [429, 500, 502, 503, 504],
        'default_headers': {
            'User-Agent': 'AutoApiTest/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
    }

    # ==================== Allure 报告 ====================
    ALLURE_CONFIG: Dict[str, Any] = {
        'enabled': True,
        'allure_bin': str(PROJECT_ROOT / 'allure-bat' / 'bin' / 'allure.bat'),
        'results_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-result'),
        'report_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-html'),
        'history_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-history'),
        'clean_results': True,
        # 写入 allure-results/environment.properties 的静态字段
        'environment_properties': {
            'Framework': 'AutoApiTest',
            'Version': '1.0',
        },
        'categories': [
            {'name': 'Ignored tests', 'matchedStatuses': ['skipped']},
            {'name': 'Product defects', 'matchedStatuses': ['failed'], 'messageRegex': '.*AssertionError.*'},
            {'name': 'Test defects', 'matchedStatuses': ['broken']},
            {'name': 'Passed tests', 'matchedStatuses': ['passed']},
        ],
    }

    # ==================== HTML 报告 ====================
    HTML_REPORT_DIR: str = str(PROJECT_ROOT / 'report' / 'html')

    # ==================== 测试运行 ====================
    RUN_CONFIG: Dict[str, Any] = {
        'workers': 1,
        'stop_on_first_failure': False,
        'max_failures': 5,
    }

    # ==================== 变量 ====================
    VARIABLE_CONFIG: Dict[str, Any] = {
        'variable_pattern': r'\$(\w+)\$',
        'persist_variables': False,
        'global_variables': {
            'env': 'test',
            'version': '1.0',
        },
        'auto_generated_variables': {
            'timestamp': 'generate_timestamp',
            'random_string': 'generate_random_string',
        },
    }

    # ==================== 邮件 ====================
    EMAIL_CONFIG: Dict[str, Any] = {
        'enabled': False,
        'smtp_server': 'smtp.example.com',
        'smtp_port': 587,
        'smtp_username': 'user@example.com',
        'smtp_password': 'password',
        'sender': 'auto_api_test@example.com',
        'receivers': ['team@example.com'],
        'subject_prefix': '[AutoApiTest] ',
    }

    # ==================== 钉钉机器人 ====================
    DINGTALK_CONFIG: Dict[str, Any] = {
        'enabled': False,
        'webhook_url': '',
        'secret': '',
        'at_mobiles': [],
        'at_all': False,
    }

    # ==================== 企业微信机器人 ====================
    WECOM_CONFIG: Dict[str, Any] = {
        'enabled': False,
        'webhook_url': '',
        'mentioned_list': [],
        'mentioned_mobile_list': [],
    }

    # ==================== 飞书机器人 ====================
    FEISHU_CONFIG: Dict[str, Any] = {
        'enabled': False,
        'webhook_url': '',
        'secret': '',
    }

    # ==================== 数据库 ====================
    DATABASE_CONFIG: Dict[str, Any] = {
        'enabled': False,
        'type': 'sqlite',          # sqlite | mysql | postgresql | sqlserver
        'host': 'localhost',
        'port': 3306,
        'database': 'autoapitest',
        'username': 'root',
        'password': '',
        'charset': 'utf8mb4',
        'pool_min_size': 2,
        'pool_max_size': 10,
    }

    # ==================== 工具方法 ====================

    @classmethod
    def get_current_env_config(cls) -> Dict[str, Any]:
        """获取当前环境的 HTTP 配置（base_url 来自子类 BASE_URL）"""
        cfg = cls.HTTP_CONFIG.copy()
        cfg['base_url'] = cls.BASE_URL
        return cfg
