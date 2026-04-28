"""开发环境配置"""

from setting.base_config import BaseConfig


class DevConfig(BaseConfig):
    # ===== 必须重写 =====
    CURRENT_ENVIRONMENT = 'dev'
    BASE_URL = 'http://dev.api.example.com'
    DESCRIPTION = '开发环境'

    # ===== 可选重写示例 =====
    # HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'verify_ssl': False}
    # LOG_CONFIG = {**BaseConfig.LOG_CONFIG, 'log_level': 'DEBUG'}
