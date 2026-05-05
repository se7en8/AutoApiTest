"""
HTTP 请求客户端
封装 requests.Session，支持变量替换和详细日志
"""
import json
import time
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import allure

from common.variable_manager import VariableManager
from common.logger import logger
from common.allure_attachments import (
    attach_request_to_allure, attach_response_to_allure, generate_curl_command
)
import setting as config


class RequestClient:
    """HTTP 请求客户端"""

    def __init__(self, base_url: str = '', variable_manager: Optional[VariableManager] = None,
                 config_override: dict = None):
        """
        初始化请求客户端

        Args:
            base_url: 基础URL，所有请求会与此拼接
            variable_manager: 变量管理器实例，如果为None则创建新的
            config_override: 覆盖 HTTP_CONFIG 的字典，便于单测注入
        """
        self.base_url = base_url.rstrip('/')
        self.variable_manager = variable_manager or VariableManager()

        http = {**config.HTTP_CONFIG, **(config_override or {})}
        self._default_timeout = http['timeout']
        self._default_verify = http['verify_ssl']
        self._default_allow_redirects = http['allow_redirects']

        # 创建会话
        self.session = requests.Session()

        # 配置重试策略（从 config 读取）
        retry_strategy = Retry(
            total=http['max_retries'],
            backoff_factor=http['retry_backoff_factor'],
            status_forcelist=http.get('retry_status_codes', [429, 500, 502, 503, 504]),
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认请求头（从 config 读取）
        self.session.headers.update(http['default_headers'])

    def request(self,
                method: str,
                url: str,
                headers: Optional[Dict[str, str]] = None,
                data: Optional[Union[Dict, str, bytes]] = None,
                json_data: Optional[Dict] = None,
                params: Optional[Dict] = None,
                timeout: Optional[int] = None,
                allow_redirects: Optional[bool] = None,
                verify: Optional[bool] = None) -> requests.Response:
        """
        发送 HTTP 请求

        Args:
            method: 请求方法 (GET, POST, PUT, DELETE, PATCH)
            url: 请求URL（可以是相对路径或绝对路径）
            headers: 请求头
            data: 请求体数据（表单数据）
            json_data: JSON 请求体数据
            params: URL 查询参数
            timeout: 超时时间（秒）
            allow_redirects: 是否允许重定向
            verify: 是否验证SSL证书

        Returns:
            requests.Response 对象
        """
        # 处理URL
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/{url.lstrip('/')}"

        # 替换URL中的变量
        url = self.variable_manager.replace_in_api_path(url)

        # 准备请求头
        request_headers = self.session.headers.copy()
        if headers:
            # 替换请求头中的变量
            headers = self.variable_manager.replace_in_headers(headers)
            request_headers.update(headers)

        # 准备请求体
        request_data = None
        request_json = None

        if json_data is not None:
            # 替换JSON数据中的变量
            request_json = self.variable_manager.replace_in_request_body(json_data)
        elif data is not None:
            if isinstance(data, dict):
                # 替换字典数据中的变量
                request_data = self.variable_manager.replace_in_request_body(data)
            else:
                # 字符串或字节数据
                request_data = self.variable_manager.replace_variables(data)

        # 替换查询参数中的变量
        if params:
            params = self.variable_manager.replace_in_request_body(params)

        # 记录请求日志
        self._log_request(method, url, request_headers, request_json or request_data, params)

        if timeout is None:
            timeout = self._default_timeout
        if allow_redirects is None:
            allow_redirects = self._default_allow_redirects
        if verify is None:
            verify = self._default_verify

        start_time = time.time()
        try:
            # 发送请求
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                data=request_data,
                json=request_json,
                params=params,
                timeout=timeout,
                allow_redirects=allow_redirects,
                verify=verify
            )
            elapsed_time = time.time() - start_time

            # 记录响应日志
            self._log_response(response, elapsed_time)

            return response

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"请求失败: {method} {url}, 耗时: {elapsed_time:.2f}s, 错误: {e}")
            raise

    def _log_request(self, method: str, url: str, headers: Dict, data: Any, params: Dict):
        """记录请求日志并附加到 Allure 报告"""
        logger.info(f"发送请求: {method.upper()} {url}")

        if params:
            logger.debug(f"请求参数: {params}")

        if headers:
            # 过滤敏感信息（如Authorization）
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                safe_headers['Authorization'] = '******'
            logger.debug(f"请求头: {safe_headers}")

        if data:
            if isinstance(data, dict):
                logger.debug(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                logger.debug(f"请求体: {data}")

        attach_request_to_allure(method, url, headers, data, params)

    def _log_response(self, response: requests.Response, elapsed_time: float):
        """记录响应日志并附加到 Allure 报告"""
        logger.info(
            f"收到响应: {response.request.method} {response.url} "
            f"状态码: {response.status_code}, 耗时: {elapsed_time:.2f}s"
        )

        try:
            response_json = response.json()
            logger.debug(f"响应体: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
        except (json.JSONDecodeError, ValueError):
            response_text = response.text
            if len(response_text) > 1000:
                response_text = response_text[:1000] + "... [截断]"
            logger.debug(f"响应体: {response_text}")

        # 附加到 Allure
        attach_response_to_allure(response, elapsed_time)

        # cURL 命令
        curl_command = generate_curl_command(response.request)
        allure.attach(
            curl_command,
            name='🔧 cURL 命令',
            attachment_type=allure.attachment_type.TEXT
        )

    # 便捷方法
    def get(self, url: str, **kwargs) -> requests.Response:
        """发送 GET 请求"""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """发送 POST 请求"""
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """发送 PUT 请求"""
        return self.request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """发送 DELETE 请求"""
        return self.request('DELETE', url, **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        """发送 PATCH 请求"""
        return self.request('PATCH', url, **kwargs)

    def set_base_url(self, base_url: str):
        """设置基础URL"""
        self.base_url = base_url.rstrip('/')

    def set_default_header(self, key: str, value: str):
        """设置默认请求头"""
        self.session.headers[key] = value

    def clear_default_headers(self):
        """清空默认请求头"""
        self.session.headers.clear()

    def get_variable_manager(self) -> VariableManager:
        """获取变量管理器"""
        return self.variable_manager

    def close(self):
        """关闭会话"""
        self.session.close()
        logger.debug("请求会话已关闭")

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭会话"""
        self.close()