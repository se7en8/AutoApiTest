"""
变量管理器
全局变量存储与读取，所有实例共享同一会话级存储
初始化时自动从 config.py 加载预定义全局变量
"""
import re
from typing import Dict, Any, Union, List
from jsonpath_ng import parse

from common.logger import logger
from common import tools
import setting as config


class VariableManager:
    """全局变量管理器 — 会话级单例，所有调用返回同一个实例"""

    _instance: 'VariableManager | None' = None
    _store: Dict[str, Any] = {}
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._load_global_variables()

    @classmethod
    def _load_global_variables(cls):
        """从 config 加载预定义全局变量并调用 tools 中的函数生成动态变量（仅首次初始化执行）"""
        if cls._loaded:
            return

        var_cfg = config.VARIABLE_CONFIG

        # 加载静态全局变量
        for var_name, var_value in var_cfg.get('global_variables', {}).items():
            cls._store[var_name] = var_value
            logger.debug(f"加载全局变量 '{var_name}' = {var_value}")

        # 调用 tools 中的函数生成动态变量
        for var_name, func_name in var_cfg.get('auto_generated_variables', {}).items():
            func = getattr(tools, func_name, None)
            if func is None or not callable(func):
                logger.warning(f"tools.py 中未找到函数 '{func_name}'，跳过变量 '{var_name}'")
                continue
            try:
                value = func()
                cls._store[var_name] = value
                logger.debug(f"执行 '{func_name}' → 变量 '{var_name}' = {value}")
            except Exception as e:
                logger.error(f"执行 '{func_name}' 失败: {e}")

        cls._loaded = True
        logger.info(f"全局变量已加载，共 {len(cls._store)} 个")

    @classmethod
    def _get_pattern(cls) -> str:
        return config.VARIABLE_CONFIG.get('variable_pattern', r'\$(\w+)\$')

    def extract_variables(self, extract_rules: Dict[str, str], response_data: Dict[str, Any],
                          multi: bool = False) -> Dict[str, Any]:
        """
        从响应数据中提取变量并存入全局存储

        Args:
            extract_rules: {变量名: jsonpath表达式}
            response_data: 响应数据
            multi: 为 True 时匹配多值返回列表；为 False 时取第一个匹配并警告多余匹配

        Returns:
            本次提取的变量字典
        """
        extracted = {}
        if not extract_rules or not response_data:
            return extracted

        for var_name, jsonpath_expr in extract_rules.items():
            jsonpath_expr = jsonpath_expr.strip()
            if not jsonpath_expr:
                continue
            try:
                expr = parse(jsonpath_expr)
                matches = expr.find(response_data)
                if matches:
                    values = [m.value for m in matches]
                    if multi:
                        extracted[var_name] = values
                        logger.debug(f"提取变量 '{var_name}' = {values} ({len(values)} 项)")
                    else:
                        extracted[var_name] = values[0]
                        if len(values) > 1:
                            logger.debug(
                                f"jsonpath 匹配多项 ({len(values)}): '{var_name}' ({jsonpath_expr})，"
                                f"已取首个值: {values[0]}，其余已忽略。请使用 multi=True 获取全部"
                            )
                        else:
                            logger.debug(f"提取变量 '{var_name}' = {extracted[var_name]}")
                else:
                    logger.warning(f"jsonpath 未匹配: '{var_name}' ({jsonpath_expr})")
            except Exception as e:
                logger.error(f"提取变量 '{var_name}' 失败: {jsonpath_expr} -> {e}")

        self._store.update(extracted)
        return extracted

    # ==================== 变量替换 ====================

    def replace_variables(self, data: Union[str, Dict, List, None]) -> Union[str, Dict, List, None]:
        """递归替换数据中的 $variable$ 占位符"""
        if isinstance(data, str):
            return self._replace_in_string(data)
        elif isinstance(data, dict):
            return self._replace_in_dict(data)
        elif isinstance(data, list):
            return self._replace_in_list(data)
        return data

    def _replace_in_string(self, text: str) -> str:
        if not text:
            return text

        def replace_match(m):
            name = m.group(1)
            if name in self._store:
                return str(self._store[name])
            logger.warning(f"变量 '${name}$' 未找到，保留占位符")
            return m.group(0)

        return re.sub(self._get_pattern(), replace_match, text)

    def _replace_in_dict(self, data: Dict) -> Dict:
        result = {}
        for k, v in data.items():
            key = self._replace_in_string(k) if isinstance(k, str) else k
            result[key] = self.replace_variables(v)
        return result

    def _replace_in_list(self, data: list) -> list:
        return [self.replace_variables(item) for item in data]

    # ==================== 全局存取 ====================

    def set_variable(self, name: str, value: Any):
        """设置变量（写入类级全局存储）"""
        self._store[name] = value
        logger.debug(f"全局变量 '{name}' = {value}")

    def get_variable(self, name: str, default: Any = None) -> Any:
        """读取变量"""
        return self._store.get(name, default)

    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量的副本"""
        return self._store.copy()

    def update_variables(self, new_variables: Dict[str, Any]):
        """批量更新变量"""
        self._store.update(new_variables)
        logger.debug(f"批量更新 {len(new_variables)} 个变量")

    @classmethod
    def clear_variables(cls):
        """清空全局存储并重置单例"""
        cls._store.clear()
        cls._loaded = False
        cls._instance = None
        logger.debug("全局变量已清空，单例已重置")

    # ==================== 便捷方法 ====================

    def replace_in_api_path(self, api_path: str) -> str:
        return self._replace_in_string(api_path)

    def replace_in_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        return self._replace_in_dict(headers)

    def replace_in_request_body(self, body: Union[Dict, List, str]) -> Union[Dict, List, str]:
        return self.replace_variables(body)
