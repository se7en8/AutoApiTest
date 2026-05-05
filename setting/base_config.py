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
    BASE_DIR: Path = PROJECT_ROOT  # 项目根目录，供其他模块拼接子路径

    # ===== 子类必须重写以下属性 =====
    CURRENT_ENVIRONMENT: str = 'dev'               # 当前环境名称 (dev/test/staging/prod)
    BASE_URL: str = 'http://dev.api.example.com'   # API 基础地址，所有相对请求拼接到此 URL
    DESCRIPTION: str = ''                          # 环境描述，用于 CLI --help 信息展示

    # ==================== 日志 ====================
    LOG_CONFIG: Dict[str, Any] = {
        'log_level': 'INFO',                # 日志级别: TRACE | DEBUG | INFO | WARNING | ERROR
        'log_dir': str(PROJECT_ROOT / 'logs'),  # 日志文件输出目录
        'log_to_console': True,             # 是否输出到控制台（rich 彩色格式化）
        'log_to_file': True,                # 是否输出到文件（按天轮转）
        'max_file_size': 10 * 1024 * 1024,  # 单个日志文件最大大小，超过触发轮转（10MB）
        'backup_count': 5,                  # 日志文件保留天数
    }

    # ==================== HTTP 请求 ====================
    HTTP_CONFIG: Dict[str, Any] = {
        'timeout': 30,                      # 请求超时时间，单位秒
        'verify_ssl': True,                 # SSL 证书校验，开发/测试环境可设为 False
        'allow_redirects': True,            # 是否跟随 HTTP 重定向
        'max_retries': 3,                   # 最大重试次数，由 urllib3 Retry 策略驱动
        'retry_backoff_factor': 1,          # 重试退避因子，延迟 = backoff_factor * (2^(retry-1))
        'retry_status_codes': [429, 500, 502, 503, 504],  # 触发重试的 HTTP 状态码
        'default_headers': {                # 每次请求自动携带的默认请求头
            'User-Agent': 'AutoApiTest/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
    }

    # ==================== Allure 报告 ====================
    ALLURE_CONFIG: Dict[str, Any] = {
        'enabled': True,                    # 总开关：是否启用 Allure 报告
        'allure_bin': 'allure',                 # allure 命令（从系统 PATH 解析，Windows 下可用 allure.bat）
        'results_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-result'),  # 测试原始结果输出目录
        'report_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-html'),      # Allure 报告 HTML 输出目录
        'history_dir': str(PROJECT_ROOT / 'report' / 'allure' / 'allure-history'),  # 历史趋势数据备份目录
        'clean_results': True,              # 每次运行前是否清空 results_dir
        'environment_properties': {         # 写入 allure-results/environment.properties 的静态字段
            'Framework': 'AutoApiTest',
            'Version': '1.0',
        },
        'categories': [                     # Allure 报告缺陷分类（自动归类用例状态）
            {'name': 'Ignored tests', 'matchedStatuses': ['skipped']},
            {'name': 'Product defects', 'matchedStatuses': ['failed'], 'messageRegex': '.*AssertionError.*'},
            {'name': 'Test defects', 'matchedStatuses': ['broken']},
            {'name': 'Passed tests', 'matchedStatuses': ['passed']},
        ],
    }

    # ==================== HTML 报告 ====================
    HTML_REPORT_DIR: str = str(PROJECT_ROOT / 'report' / 'html')  # pytest-html 报告输出目录

    # ==================== 测试运行 ====================
    RUN_CONFIG: Dict[str, Any] = {
        'workers': 1,                       # 并行工作进程数，1 为串行，>1 使用 pytest-xdist 并行
        'stop_on_first_failure': False,     # 首次失败即停止（同 pytest --maxfail=1）
        'max_failures': 5,                  # 最大失败数，超过后终止运行
    }

    # ==================== 变量 ====================
    VARIABLE_CONFIG: Dict[str, Any] = {
        'variable_pattern': r'\$(\w+)\$',   # 占位符正则，匹配 $var_name$ 格式
        'persist_variables': False,         # 会话结束后是否保留变量（跨 session 共享）
        'global_variables': {               # 预定义的静态全局变量，初始化时自动加载
            'env': 'test',
            'version': '1.0',
        },
        'auto_generated_variables': {       # 动态变量：键为变量名，值为 common/tools.py 中的函数名
            'timestamp': 'generate_timestamp',         # → tools.generate_timestamp()
            'random_string': 'generate_random_string', # → tools.generate_random_string()
        },
    }

    # ==================== 邮件 ====================
    EMAIL_CONFIG: Dict[str, Any] = {
        'enabled': False,                   # 是否启用邮件通知
        'smtp_server': 'smtp.example.com',  # SMTP 服务器地址
        'smtp_port': 587,                   # SMTP 端口（587=STARTTLS, 465=SSL）
        'smtp_username': 'user@example.com',# SMTP 认证用户名
        'smtp_password': 'password',        # SMTP 认证密码
        'sender': 'auto_api_test@example.com',  # 发件人地址
        'receivers': ['team@example.com'],  # 默认收件人列表
        'subject_prefix': '[AutoApiTest] ', # 邮件主题前缀
    }

    # ==================== 钉钉机器人 ====================
    DINGTALK_CONFIG: Dict[str, Any] = {
        'enabled': False,                   # 是否启用钉钉通知
        'webhook_url': '',                  # 钉钉群机器人 Webhook 地址
        'secret': '',                       # 加签密钥（用于 HMAC-SHA256 签名验证），为空则不签名
        'at_mobiles': [],                   # 默认 @ 的手机号列表
        'at_all': False,                    # 是否默认 @所有人
    }

    # ==================== 企业微信机器人 ====================
    WECOM_CONFIG: Dict[str, Any] = {
        'enabled': False,                   # 是否启用企业微信通知
        'webhook_url': '',                  # 企业微信群机器人 Webhook 地址
        'mentioned_list': [],               # 默认 @ 的成员 ID 列表
        'mentioned_mobile_list': [],        # 默认 @ 的手机号列表
    }

    # ==================== 飞书机器人 ====================
    FEISHU_CONFIG: Dict[str, Any] = {
        'enabled': False,                   # 是否启用飞书通知
        'webhook_url': '',                  # 飞书群机器人 Webhook 地址
        'secret': '',                       # 加签密钥（用于 HMAC-SHA256 签名验证），为空则不签名
    }

    # ==================== 数据库 ====================
    DATABASE_CONFIG: Dict[str, Any] = {
        'enabled': False,                   # 总开关：True 时 database fixture 才创建连接池
        'type': 'sqlite',                   # 数据库类型: sqlite | mysql | postgresql | sqlserver
        'host': 'localhost',                # 数据库主机（SQLite 忽略此字段）
        'port': 3306,                       # 端口（MySQL 3306, PostgreSQL 5432, SQL Server 1433）
        'database': 'autoapitest',          # 数据库名（SQLite 时为文件路径，:memory: 为内存库）
        'username': 'root',                 # 用户名
        'password': '',                     # 密码
        'charset': 'utf8mb4',               # 字符集（仅 MySQL 使用）
        'pool_min_size': 2,                 # 连接池最小空闲连接数
        'pool_max_size': 10,                # 连接池最大连接数（实际最大连接 = 2x 此值）
    }

    # ==================== 工具方法 ====================

    @classmethod
    def get_current_env_config(cls) -> Dict[str, Any]:
        """获取当前环境的 HTTP 配置（base_url 来自子类 BASE_URL）"""
        cfg = cls.HTTP_CONFIG.copy()
        cfg['base_url'] = cls.BASE_URL
        return cfg
