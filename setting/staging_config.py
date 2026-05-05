"""预发布环境配置"""

from setting.base_config import BaseConfig


class StagingConfig(BaseConfig):
    CURRENT_ENVIRONMENT = 'staging'
    BASE_URL = 'http://staging.api.example.com'
    DESCRIPTION = '预发布环境'

    # 预发布：保持生产级配置但延长 timeout 以应对冷启动
    HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'timeout': 60}
