"""测试环境配置"""

from setting.base_config import BaseConfig


class TestConfig(BaseConfig):
    CURRENT_ENVIRONMENT = 'test'
    BASE_URL = 'http://localhost:8000'
    DESCRIPTION = '测试环境'

    # 测试环境：关闭 SSL，延长超时（可能有调试断点）
    HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'verify_ssl': False, 'timeout': 60}
