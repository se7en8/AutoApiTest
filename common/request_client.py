"""
HTTP 请求客户端
封装 requests.Session，支持变量替换和详细日志
支持 Allure 报告记录请求和响应信息
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
import setting as config


class RequestClient:
    """HTTP 请求客户端"""

    def __init__(self, base_url: str = '', variable_manager: Optional[VariableManager] = None):
        """
        初始化请求客户端

        Args:
            base_url: 基础URL，所有请求会与此拼接
            variable_manager: 变量管理器实例，如果为None则创建新的
        """
        self.base_url = base_url.rstrip('/')
        self.variable_manager = variable_manager or VariableManager()

        http = config.HTTP_CONFIG
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

        # 附加请求信息到 Allure 报告
        self._attach_request_to_allure(method, url, headers, data, params)

    def _attach_request_to_allure(self, method: str, url: str, headers: Dict, data: Any, params: Dict):
        """将请求信息以 HTML 格式附加到 Allure 报告"""
        html = self._build_request_html(method, url, headers, data, params)
        allure.attach(
            html,
            name=f'📤 Request: {method.upper()}',
            attachment_type=allure.attachment_type.HTML
        )

    def _build_request_html(self, method: str, url: str, headers: Dict, data: Any, params: Dict) -> str:
        """构建请求信息的 HTML"""
        method_colors = {
            'GET': '#4CAF50', 'POST': '#2196F3', 'PUT': '#FF9800',
            'DELETE': '#f44336', 'PATCH': '#9C27B0',
        }
        color = method_colors.get(method.upper(), '#607D8B')

        rows = []

        # 请求行
        rows.append(f'''<tr>
            <td class="label">Request Line</td>
            <td><span class="method" style="background:{color}">{method.upper()}</span>
                <code style="margin-left:8px">{self._escape_html(url)}</code></td>
        </tr>''')

        # 请求头
        if headers:
            safe_headers = self._convert_to_dict(headers)
            for k in list(safe_headers.keys()):
                if k.lower() == 'authorization':
                    v = safe_headers[k]
                    safe_headers[k] = f"Bearer ***{v[-6:]}" if len(v) > 20 and v.startswith('Bearer ') else '******'
            hrows = ''.join(
                f'<tr><td class="label sub">{self._escape_html(k)}</td>'
                f'<td><code>{self._escape_html(str(v))}</code></td></tr>'
                for k, v in safe_headers.items()
            )
            rows.append(f'''<tr>
                <td class="label">Headers</td>
                <td><table class="sub-table">{hrows}</table></td>
            </tr>''')
        else:
            rows.append('<tr><td class="label">Headers</td><td><em>—</em></td></tr>')

        # 查询参数
        if params:
            prows = ''.join(
                f'<tr><td class="label sub">{self._escape_html(str(k))}</td>'
                f'<td><code>{self._escape_html(str(v))}</code></td></tr>'
                for k, v in self._convert_to_dict(params).items()
            )
            rows.append(f'''<tr>
                <td class="label">Query Params</td>
                <td><table class="sub-table">{prows}</table></td>
            </tr>''')
        else:
            rows.append('<tr><td class="label">Query Params</td><td><em>—</em></td></tr>')

        # 请求体
        body_html = ''
        if data:
            if isinstance(data, (dict, list)):
                body_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                body_str = str(data)
            body_html = f'<pre class="json">{self._escape_html(body_str)}</pre>'
        else:
            body_html = '<em>—</em>'
        rows.append(f'<tr><td class="label">Body</td><td>{body_html}</td></tr>')

        return self._wrap_html(
            title=f'📤 {method.upper()} Request',
            rows='\n'.join(rows)
        )

    def _log_response(self, response: requests.Response, elapsed_time: float):
        """记录响应日志并附加到 Allure 报告"""
        logger.info(
            f"收到响应: {response.request.method} {response.url} "
            f"状态码: {response.status_code}, 耗时: {elapsed_time:.2f}s"
        )

        try:
            # 尝试解析JSON响应
            response_json = response.json()
            logger.debug(f"响应体: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
        except (json.JSONDecodeError, ValueError):
            # 非JSON响应
            response_text = response.text
            if len(response_text) > 1000:
                response_text = response_text[:1000] + "... [截断]"
            logger.debug(f"响应体: {response_text}")

        # 附加响应信息到 Allure 报告
        self._attach_response_to_allure(response, elapsed_time)

    def _attach_response_to_allure(self, response: requests.Response, elapsed_time: float):
        """将响应信息以 HTML 格式附加到 Allure 报告"""
        html = self._build_response_html(response, elapsed_time)
        allure.attach(
            html,
            name=f'📥 Response: {response.status_code} {response.reason}',
            attachment_type=allure.attachment_type.HTML
        )

        # cURL 仍保留 TEXT 格式，便于复制
        curl_command = self._generate_curl_command(response.request)
        allure.attach(
            curl_command,
            name='🔧 cURL 命令',
            attachment_type=allure.attachment_type.TEXT
        )

    def _build_response_html(self, response: requests.Response, elapsed_time: float) -> str:
        """构建响应信息的 HTML"""
        sc = response.status_code
        if sc < 300:
            badge = f'<span class="badge success">{sc}</span>'
        elif sc < 400:
            badge = f'<span class="badge warning">{sc}</span>'
        else:
            badge = f'<span class="badge error">{sc}</span>'

        rows = [
            f'<tr><td class="label">Status</td><td>{badge} {self._escape_html(response.reason)}</td></tr>',
            f'<tr><td class="label">URL</td><td><code>{self._escape_html(response.url)}</code></td></tr>',
            f'<tr><td class="label">Time</td><td><code>{elapsed_time:.3f}s</code></td></tr>',
        ]

        # 响应头
        if response.headers:
            hrows = ''.join(
                f'<tr><td class="label sub">{self._escape_html(k)}</td>'
                f'<td><code>{self._escape_html(str(v))}</code></td></tr>'
                for k, v in self._convert_to_dict(response.headers).items()
            )
            rows.append(f'''<tr>
                <td class="label">Headers</td>
                <td><table class="sub-table">{hrows}</table></td>
            </tr>''')

        # 响应体
        try:
            body_json = response.json()
            body_str = json.dumps(body_json, ensure_ascii=False, indent=2, default=str)
        except (json.JSONDecodeError, ValueError):
            body_str = response.text[:5000]
            if len(response.text) > 5000:
                body_str += '\n... [truncated]'

        rows.append(f'''<tr>
            <td class="label">Body</td>
            <td><pre class="json">{self._escape_html(body_str)}</pre></td>
        </tr>''')

        return self._wrap_html(
            title=f'📥 Response: {sc} {response.reason}',
            rows='\n'.join(rows)
        )

    def _convert_to_dict(self, obj: Any) -> dict:
        """安全地将对象转换为普通字典"""
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return {str(k): v for k, v in obj.items()}
        if hasattr(obj, 'items'):
            return {str(k): v for k, v in obj.items()}
        return dict(obj) if obj else {}

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML 特殊字符"""
        if not isinstance(text, str):
            text = str(text)
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
                )

    @staticmethod
    def _wrap_html(title: str, rows: str) -> str:
        """包装 HTML 文档"""
        return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           margin: 16px; background: #fafafa; }}
    h3 {{ margin: 0 0 12px 0; color: #333; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td {{ padding: 6px 10px; vertical-align: top; border-bottom: 1px solid #e0e0e0; }}
    td.label {{ width: 130px; font-weight: 600; color: #555; white-space: nowrap; }}
    td.label.sub {{ width: auto; font-weight: 400; color: #666; padding-left: 16px; }}
    .method {{ display: inline-block; padding: 2px 8px; border-radius: 3px;
              color: #fff; font-weight: 700; font-size: 12px; }}
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 3px;
              color: #fff; font-weight: 700; font-size: 14px; }}
    .success {{ background: #4CAF50; }}
    .warning {{ background: #FF9800; }}
    .error {{ background: #f44336; }}
    code {{ font-family: 'SF Mono', 'Consolas', 'Liberation Mono', monospace;
            font-size: 12px; background: #f5f5f5; padding: 1px 4px; border-radius: 2px;
            word-break: break-all; }}
    pre.json {{ font-family: 'SF Mono', 'Consolas', 'Liberation Mono', monospace;
                font-size: 12px; background: #f5f5f5; padding: 10px; border-radius: 4px;
                overflow-x: auto; margin: 0; white-space: pre-wrap; word-break: break-all; }}
    .sub-table {{ width: 100%; }}
    .sub-table td {{ border: none; padding: 2px 4px; font-size: 12px; }}
    em {{ color: #999; }}
</style></head>
<body>
<h3>{title}</h3>
<table>{rows}</table>
</body>
</html>'''

    def _generate_curl_command(self, prepared_request) -> str:
        """生成 cURL 命令"""
        parts = [f"curl -X {prepared_request.method}"]

        # 添加请求头
        for key, value in prepared_request.headers.items():
            # 跳过一些自动添加的头
            if key.lower() in ('host', 'content-length', 'accept-encoding'):
                continue
            parts.append(f"  -H '{key}: {value}'")

        # 添加请求体
        if prepared_request.body:
            if isinstance(prepared_request.body, bytes):
                try:
                    body = prepared_request.body.decode('utf-8')
                except UnicodeDecodeError:
                    body = str(prepared_request.body)
            else:
                body = prepared_request.body

            # 转义单引号
            body = body.replace("'", "'\\''")
            parts.append(f"  -d '{body}'")

        # 添加URL
        parts.append(f"  '{prepared_request.url}'")

        return ' \\\n'.join(parts)

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