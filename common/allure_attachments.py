"""
Allure 报告 HTML 附件生成
从 RequestClient 中抽离，保持纯粹的 HTML 模板拼接逻辑
"""
import json
from typing import Any, Dict

import allure
import requests


def escape_html(text: str) -> str:
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


def _convert_to_dict(obj: Any) -> dict:
    """安全地将对象转换为普通字典"""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return {str(k): v for k, v in obj.items()}
    if hasattr(obj, 'items'):
        return {str(k): v for k, v in obj.items()}
    return dict(obj) if obj else {}


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


def build_request_html(method: str, url: str, headers: Dict, data: Any, params: Dict) -> str:
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
            <code style="margin-left:8px">{escape_html(url)}</code></td>
    </tr>''')

    # 请求头
    if headers:
        safe_headers = _convert_to_dict(headers)
        for k in list(safe_headers.keys()):
            if k.lower() == 'authorization':
                v = safe_headers[k]
                safe_headers[k] = f"Bearer ***{v[-6:]}" if len(v) > 20 and v.startswith('Bearer ') else '******'
        hrows = ''.join(
            f'<tr><td class="label sub">{escape_html(k)}</td>'
            f'<td><code>{escape_html(str(v))}</code></td></tr>'
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
            f'<tr><td class="label sub">{escape_html(str(k))}</td>'
            f'<td><code>{escape_html(str(v))}</code></td></tr>'
            for k, v in _convert_to_dict(params).items()
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
        body_html = f'<pre class="json">{escape_html(body_str)}</pre>'
    else:
        body_html = '<em>—</em>'
    rows.append(f'<tr><td class="label">Body</td><td>{body_html}</td></tr>')

    return _wrap_html(
        title=f'📤 {method.upper()} Request',
        rows='\n'.join(rows)
    )


def build_response_html(response: requests.Response, elapsed_time: float) -> str:
    """构建响应信息的 HTML"""
    sc = response.status_code
    if sc < 300:
        badge = f'<span class="badge success">{sc}</span>'
    elif sc < 400:
        badge = f'<span class="badge warning">{sc}</span>'
    else:
        badge = f'<span class="badge error">{sc}</span>'

    rows = [
        f'<tr><td class="label">Status</td><td>{badge} {escape_html(response.reason)}</td></tr>',
        f'<tr><td class="label">URL</td><td><code>{escape_html(response.url)}</code></td></tr>',
        f'<tr><td class="label">Time</td><td><code>{elapsed_time:.3f}s</code></td></tr>',
    ]

    # 响应头
    if response.headers:
        hrows = ''.join(
            f'<tr><td class="label sub">{escape_html(k)}</td>'
            f'<td><code>{escape_html(str(v))}</code></td></tr>'
            for k, v in _convert_to_dict(response.headers).items()
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
        <td><pre class="json">{escape_html(body_str)}</pre></td>
    </tr>''')

    return _wrap_html(
        title=f'📥 Response: {sc} {response.reason}',
        rows='\n'.join(rows)
    )


def attach_request_to_allure(method: str, url: str, headers: Dict, data: Any, params: Dict):
    """将请求信息以 HTML 格式附加到 Allure 报告"""
    html = build_request_html(method, url, headers, data, params)
    allure.attach(
        html,
        name=f'📤 Request: {method.upper()}',
        attachment_type=allure.attachment_type.HTML
    )


def attach_response_to_allure(response: requests.Response, elapsed_time: float):
    """将响应信息以 HTML 格式附加到 Allure 报告"""
    html = build_response_html(response, elapsed_time)
    allure.attach(
        html,
        name=f'📥 Response: {response.status_code} {response.reason}',
        attachment_type=allure.attachment_type.HTML
    )


def generate_curl_command(prepared_request) -> str:
    """生成 cURL 命令"""
    parts = [f"curl -X {prepared_request.method}"]

    for key, value in prepared_request.headers.items():
        if key.lower() in ('host', 'content-length', 'accept-encoding'):
            continue
        parts.append(f"  -H '{key}: {value}'")

    if prepared_request.body:
        if isinstance(prepared_request.body, bytes):
            try:
                body = prepared_request.body.decode('utf-8')
            except UnicodeDecodeError:
                body = str(prepared_request.body)
        else:
            body = prepared_request.body
        body = body.replace("'", "'\\''")
        parts.append(f"  -d '{body}'")

    parts.append(f"  '{prepared_request.url}'")

    return ' \\\n'.join(parts)
