"""
配置模块
自动扫描 setting/ 目录下所有 *_config.py，发现继承 BaseConfig 的配置类

新增环境只需创建一个 xx_config.py 文件，无需修改任何现有代码:
    1. 复制 dev_config.py → uat_config.py
    2. 修改 CURRENT_ENVIRONMENT / BASE_URL / DESCRIPTION
    3. 即自动注册，可通过 --environment=uat 使用

用法:
    import setting as config
    print(config.BASE_URL)
    print(config.get_current_env_config()['base_url'])

切换环境:
    from setting import reload_config
    reload_config('prod')
"""
import sys
import importlib
from pathlib import Path
from typing import Type, Any

from setting.base_config import BaseConfig

# {环境名: 配置类}，自动扫描填充
_ENV_REGISTRY: dict = {}
_active: Type[BaseConfig] = None


def _discover_configs():
    """扫描 setting/ 目录，自动发现所有 *_config.py 中继承 BaseConfig 的类"""
    setting_dir = Path(__file__).parent
    for path in sorted(setting_dir.glob('*_config.py')):
        if path.stem == 'base_config':
            continue
        module = importlib.import_module(f'setting.{path.stem}')
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseConfig)
                and obj is not BaseConfig
                and hasattr(obj, 'CURRENT_ENVIRONMENT')
            ):
                _ENV_REGISTRY[obj.CURRENT_ENVIRONMENT] = obj
    if not _ENV_REGISTRY:
        raise RuntimeError("未发现任何环境配置类，请检查 setting/ 目录")


_discover_configs()


def load_config(environment: str) -> Type[BaseConfig]:
    """加载指定环境的配置类"""
    global _active
    cls = _ENV_REGISTRY.get(environment)
    if cls is None:
        raise ValueError(f"未知环境: {environment}，可用: {list(_ENV_REGISTRY.keys())}")
    _active = cls
    return _active


def get_config() -> Type[BaseConfig]:
    """获取当前活动的配置类（未加载时默认 dev）"""
    global _active
    if _active is None:
        load_config('dev')
    return _active


def reload_config(environment: str) -> Type[BaseConfig]:
    """切换环境配置"""
    return load_config(environment)


def get_active_env() -> str:
    """获取当前活动环境名称"""
    return get_config().CURRENT_ENVIRONMENT


def get_available_envs() -> dict:
    """获取自动发现的可用环境列表 {env_name: description}"""
    return {
        env: getattr(cls, 'DESCRIPTION', '')
        for env, cls in _ENV_REGISTRY.items()
    }


# ==================== 模块级别属性代理 ====================

def __getattr__(name: str) -> Any:
    """将所有未定义的属性访问代理到当前活动的配置类（首次访问时惰性加载 dev）"""
    if name.startswith('_'):
        raise AttributeError(name)
    cfg = get_config()
    if hasattr(cfg, name):
        return getattr(cfg, name)
    raise AttributeError(f"module 'setting' has no attribute '{name}'")


def __dir__():
    """支持 dir() 和 IDE 补全"""
    cfg = get_config()
    base = list(globals().keys())
    base.extend(attr for attr in dir(cfg) if not attr.startswith('_'))
    return sorted(set(base))


# ==================== 安全打印 ====================

def _safe_print(message):
    if not isinstance(message, str):
        message = str(message)
    try:
        print(message)
    except (UnicodeEncodeError, AttributeError):
        try:
            sys.stdout.buffer.write(message.encode('utf-8') + b'\n')
            sys.stdout.flush()
        except Exception:
            try:
                sys.stdout.write(message.encode('utf-8', 'replace').decode('utf-8', 'replace') + '\n')
                sys.stdout.flush()
            except Exception:
                try:
                    sys.stdout.write(repr(message) + '\n')
                    sys.stdout.flush()
                except Exception:
                    pass


# ==================== 启动 ====================

# 惰性加载：首次访问 config 属性时 get_config() 自动加载 dev
# 实际环境由 run_tests.py 或 conftest.py 在解析 CLI 参数后通过 reload_config 设定

