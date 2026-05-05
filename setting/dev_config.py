"""开发环境配置"""

from setting.base_config import BaseConfig


class DevConfig(BaseConfig):
    CURRENT_ENVIRONMENT = 'dev'
    BASE_URL = 'http://dev.api.example.com'
    DESCRIPTION = '开发环境'

    # 开发环境：关闭 SSL 验证，开启 DEBUG 日志
    HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'verify_ssl': False}
    LOG_CONFIG = {**BaseConfig.LOG_CONFIG, 'log_level': 'DEBUG'}
