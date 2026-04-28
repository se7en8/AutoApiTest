"""测试环境配置"""

from setting.base_config import BaseConfig


class TestConfig(BaseConfig):
    # ===== 必须重写 =====
    CURRENT_ENVIRONMENT = 'test'
    BASE_URL = 'http://localhost:8000'
    DESCRIPTION = '测试环境'

    # ===== 可选重写示例 =====
    # HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'verify_ssl': False, 'timeout': 60}
