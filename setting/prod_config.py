"""生产环境配置"""

from setting.base_config import BaseConfig


class ProdConfig(BaseConfig):
    CURRENT_ENVIRONMENT = 'prod'
    BASE_URL = 'https://api.example.com'
    DESCRIPTION = '生产环境（只读）'

    # 生产环境：减少日志级别，避免输出敏感信息
    LOG_CONFIG = {
        **BaseConfig.LOG_CONFIG,
        'log_level': 'WARNING',
        'log_to_console': False,
    }
    # 生产环境：减少日志文件体积
    ALLURE_CONFIG = {
        **BaseConfig.ALLURE_CONFIG,
        'enabled': True,
    }
