"""生产环境配置"""

from setting.base_config import BaseConfig


class ProdConfig(BaseConfig):
    # ===== 必须重写 =====
    CURRENT_ENVIRONMENT = 'prod'
    BASE_URL = 'https://api.example.com'
    DESCRIPTION = '生产环境（只读）'

    # ===== 可选重写示例 =====
    # LOG_CONFIG = {**BaseConfig.LOG_CONFIG, 'log_level': 'WARNING'}
