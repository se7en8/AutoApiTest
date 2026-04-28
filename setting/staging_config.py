"""预发布环境配置"""

from setting.base_config import BaseConfig


class StagingConfig(BaseConfig):
    # ===== 必须重写 =====
    CURRENT_ENVIRONMENT = 'staging'
    BASE_URL = 'http://staging.api.example.com'
    DESCRIPTION = '预发布环境'
