# """
# API 测试用例模板
# 基于 Python 编写的测试用例执行测试
# """
# import pytest
# import allure
# from typing import Dict, Any
# from common.logger import logger


# class TestApiTemplate:
#     """API 测试模板类"""

#     @pytest.mark.api
#     def test_api_case(self, test_case_data: Dict[str, Any], request_client, variable_manager):
#         """
#         执行 API 测试用例

#         Args:
#             test_case_data: 测试用例数据
#             request_client: 请求客户端
#             variable_manager: 变量管理器
#         """
#         # 检查测试用例是否启用
#         if not test_case_data.get('enabled', True):
#             pytest.skip(f"测试用例 {test_case_data.get('test_id', 'unknown')} 已禁用")

#         test_id = test_case_data.get('test_id', 'unknown')
#         logger.info(f"开始执行测试用例: {test_id}")

#         # 准备测试数据
#         api_path = test_case_data.get('api', {}).get('api_path', '')
#         method = test_case_data.get('api', {}).get('method', 'GET')
#         headers = test_case_data.get('api', {}).get('headers', {})
#         request_body = test_case_data.get('api', {}).get('request_body', {})
#         expected_status = test_case_data.get('assertion', {}).get('expected_status')
#         expected_response = test_case_data.get('assertion', {}).get('expected_response', {})
#         extract_rules = test_case_data.get('assertion', {}).get('extract_rules', {})

#         # 检查依赖关系
#         depends_on = test_case_data.get('depends_on', '')
#         if depends_on:
#             logger.info(f"测试用例 {test_id} 依赖: {depends_on}")
#             # 这里可以添加依赖检查逻辑
#             # 例如：确保依赖的测试用例已执行并成功

#         # 发送请求
#         try:
#             response = request_client.request(
#                 method=method,
#                 url=api_path,
#                 headers=headers,
#                 json_data=request_body if request_body else None
#             )
#         except Exception as e:
#             logger.error(f"请求失败: {e}")
#             pytest.fail(f"请求失败: {e}")

#         # 提取变量
#         if extract_rules and response.status_code < 400:  # 只在成功响应时提取变量
#             try:
#                 response_json = response.json()
#                 extracted = variable_manager.extract_variables(extract_rules, response_json)
#                 if extracted:
#                     logger.info(f"从响应中提取变量: {extracted}")
#             except Exception as e:
#                 logger.warning(f"变量提取失败: {e}")

#         # 替换预期响应中的变量占位符
#         if expected_response:
#             expected_response = variable_manager.replace_variables(expected_response)

#         # 断言响应
#         self._assert_response(response, expected_status, expected_response, test_id)

#         logger.info(f"测试用例 {test_id} 执行完成")

#     def _assert_response(self, response, expected_status, expected_response, test_id):
#         """
#         断言响应

#         Args:
#             response: 响应对象
#             expected_status: 期望状态码
#             expected_response: 期望响应内容
#             test_id: 测试用例ID
#         """
#         # 断言状态码
#         if expected_status is not None:
#             assert response.status_code == expected_status, \
#                 f"测试用例 {test_id}: 状态码断言失败 - " \
#                 f"期望: {expected_status}, 实际: {response.status_code}"

#         # 断言响应内容
#         if expected_response:
#             try:
#                 actual_response = response.json() if response.content else {}
#                 self._assert_response_content(actual_response, expected_response, test_id)
#             except ValueError:
#                 # 响应不是 JSON 格式
#                 actual_text = response.text
#                 if isinstance(expected_response, str):
#                     assert expected_response in actual_text, \
#                         f"测试用例 {test_id}: 响应文本断言失败 - " \
#                         f"期望包含: {expected_response}, 实际: {actual_text[:200]}..."
#                 else:
#                     pytest.fail(f"测试用例 {test_id}: 期望响应是JSON但实际是文本")

#     def _assert_response_content(self, actual_response, expected_response, test_id):
#         """
#         断言响应内容

#         Args:
#             actual_response: 实际响应内容（字典）
#             expected_response: 期望响应内容（字典）
#             test_id: 测试用例ID
#         """
#         # 递归检查响应字段
#         self._check_response_fields(actual_response, expected_response, [], test_id)

#     def _check_response_fields(self, actual, expected, path, test_id):
#         """
#         递归检查响应字段

#         Args:
#             actual: 实际值
#             expected: 期望值
#             path: 当前路径（用于错误消息）
#             test_id: 测试用例ID
#         """
#         if isinstance(expected, dict) and isinstance(actual, dict):
#             for key, expected_value in expected.items():
#                 current_path = path + [str(key)]
#                 if key not in actual:
#                     pytest.fail(
#                         f"测试用例 {test_id}: 字段缺失 - "
#                         f"路径: {' -> '.join(current_path)}"
#                     )
#                 self._check_response_fields(actual[key], expected_value, current_path, test_id)
#         elif isinstance(expected, list) and isinstance(actual, list):
#             if len(expected) != len(actual):
#                 pytest.fail(
#                     f"测试用例 {test_id}: 数组长度不匹配 - "
#                     f"路径: {' -> '.join(path)}, 期望: {len(expected)}, 实际: {len(actual)}"
#                 )
#             for i, (expected_item, actual_item) in enumerate(zip(expected, actual)):
#                 current_path = path + [f"[{i}]"]
#                 self._check_response_fields(actual_item, expected_item, current_path, test_id)
#         else:
#             # 基本类型比较（支持宽松类型转换）
#             if expected is not None and not self._values_match(actual, expected):
#                 pytest.fail(
#                     f"测试用例 {test_id}: 值不匹配 - "
#                     f"路径: {' -> '.join(path) if path else '根'}, "
#                     f"期望: {expected} (类型: {type(expected).__name__}), "
#                     f"实际: {actual} (类型: {type(actual).__name__})"
#                 )

#     def _values_match(self, actual, expected):
#         """
#         比较实际值和期望值，支持宽松类型转换

#         Args:
#             actual: 实际值
#             expected: 期望值

#         Returns:
#             bool: 是否匹配
#         """
#         # 如果直接相等，直接返回 True
#         if actual == expected:
#             return True

#         # 尝试类型转换后比较
#         try:
#             # 如果 expected 是字符串，actual 是数字，尝试转换
#             if isinstance(expected, str) and isinstance(actual, (int, float)):
#                 # 尝试将字符串转换为数字
#                 if '.' in expected:
#                     converted = float(expected)
#                 else:
#                     converted = int(expected)
#                 return converted == actual
#             elif isinstance(expected, (int, float)) and isinstance(actual, str):
#                 # 如果 expected 是数字，actual 是字符串，尝试转换
#                 try:
#                     if isinstance(expected, float) or '.' in actual:
#                         converted = float(actual)
#                     else:
#                         converted = int(actual)
#                     return converted == expected
#                 except ValueError:
#                     pass
#             # 对于布尔值转换
#             elif isinstance(expected, bool) and isinstance(actual, str):
#                 # 字符串 "true"/"false" 转换为布尔值
#                 lower_actual = actual.lower()
#                 if lower_actual in ('true', 'false'):
#                     converted = lower_actual == 'true'
#                     return converted == expected
#             elif isinstance(expected, str) and isinstance(actual, bool):
#                 # 布尔值转换为字符串 "True"/"False"
#                 converted = str(actual)
#                 return converted.lower() == expected.lower()
#         except Exception:
#             pass

#         # 最后尝试字符串比较
#         return str(actual) == str(expected)

#     @pytest.mark.smoke
#     def test_smoke(self, request_client):
#         """
#         冒烟测试：检查 API 基本可用性
#         """
#         # 这里可以添加基本的健康检查
#         # 例如：检查首页、健康检查端点等
#         logger.info("执行冒烟测试")

#         # 示例：检查根端点
#         try:
#             response = request_client.get('/')
#             assert response.status_code < 500, f"服务器错误: {response.status_code}"
#             logger.info("冒烟测试通过")
#         except Exception as e:
#             pytest.fail(f"冒烟测试失败: {e}")

# # 自定义测试钩子函数示例
# def setup_login():
#     """登录前置钩子示例"""
#     logger.info("执行登录前置操作")


# def teardown_login():
#     """登录后置钩子示例"""
#     logger.info("执行登录后置操作")