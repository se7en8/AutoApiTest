"""
API 请求与变量读写测试
"""
import pytest
from common.variable_manager import VariableManager
from common.logger import logger


class TestVariableReadWrite:
    """变量存取测试"""

    def test_set_and_get(self, variable_manager):
        """写入后立即读取"""
        variable_manager.set_variable("my_key", "my_value")
        assert variable_manager.get_variable("my_key") == "my_value"

    def test_get_nonexistent_returns_default(self, variable_manager):
        """读取不存在的变量返回默认值"""
        assert variable_manager.get_variable("no_such_key") is None
        assert variable_manager.get_variable("no_such_key", "fallback") == "fallback"

    def test_cross_instance_sharing(self, variable_manager):
        """类级存储：不同实例共享同一份变量数据"""
        variable_manager.set_variable("shared", "from_first")
        another = VariableManager()
        assert another.get_variable("shared") == "from_first"

    def test_replace_in_string(self, variable_manager):
        """替换字符串中的 $var$ 占位符"""
        variable_manager.set_variable("user", "alice")
        result = variable_manager.replace_variables("Hello, $user$!")
        assert result == "Hello, alice!"

    def test_replace_in_dict(self, variable_manager):
        """替换字典中的占位符"""
        variable_manager.set_variable("token", "abc123")
        data = {"Authorization": "Bearer $token$", "fixed": "value"}
        result = variable_manager.replace_variables(data)
        assert result["Authorization"] == "Bearer abc123"
        assert result["fixed"] == "value"

    def test_replace_in_list(self, variable_manager):
        """替换列表中的占位符"""
        variable_manager.set_variable("id", "42")
        result = variable_manager.replace_variables(["$id$", "static", "$id$"])
        assert result == ["42", "static", "42"]

    def test_missing_variable_keeps_placeholder(self, variable_manager):
        """未找到变量时保留原占位符"""
        result = variable_manager.replace_variables("$ghost$")
        assert "$ghost$" in result

    def test_bulk_update_and_get_all(self, variable_manager):
        """批量更新并获取全部变量"""
        variable_manager.update_variables({"a": 1, "b": 2})
        all_vars = variable_manager.get_all_variables()
        assert all_vars["a"] == 1
        assert all_vars["b"] == 2

    def test_global_variables_present(self, variable_manager):
        """conftest 注入的全局变量 timestamp / random_string 存在"""
        ts = variable_manager.get_variable("timestamp")
        rs = variable_manager.get_variable("random_string")
        assert ts is not None, "timestamp 全局变量未设置"
        assert rs is not None, "random_string 全局变量未设置"
        assert isinstance(ts, int)
        assert isinstance(rs, str) and len(rs) == 8


class TestJsonPathExtraction:
    """JSONPath 变量提取测试"""

    def test_extract_from_response(self, variable_manager):
        """从模拟响应数据中提取变量"""
        response = {"code": 0, "data": {"token": "x-token-999", "user": {"id": 1001}}}
        rules = {
            "token": "$.data.token",
            "user_id": "$.data.user.id",
        }
        extracted = variable_manager.extract_variables(rules, response)
        assert extracted["token"] == "x-token-999"
        assert extracted["user_id"] == 1001
        # 提取后应可通过 get_variable 读取
        assert variable_manager.get_variable("token") == "x-token-999"

    def test_extract_missing_path(self, variable_manager):
        """jsonpath 无匹配时不提取"""
        response = {"data": {}}
        extracted = variable_manager.extract_variables({"ghost": "$.data.nonexistent"}, response)
        assert "ghost" not in extracted


class TestVariableInApiPath:
    """变量在 API 路径/请求头中的替换"""

    def test_replace_in_api_path(self, variable_manager):
        variable_manager.set_variable("uid", "100")
        result = variable_manager.replace_in_api_path("/users/$uid$/profile")
        assert result == "/users/100/profile"

    def test_replace_in_headers(self, variable_manager):
        variable_manager.set_variable("token", "secret123")
        headers = {"Authorization": "Bearer $token$"}
        result = variable_manager.replace_in_headers(headers)
        assert result["Authorization"] == "Bearer secret123"

    def test_replace_in_request_body(self, variable_manager):
        variable_manager.set_variable("name", "bob")
        body = {"username": "$name$", "role": "admin"}
        result = variable_manager.replace_in_request_body(body)
        assert result["username"] == "bob"


# class TestApiRequest:
#     """API 请求测试"""

#     @pytest.mark.api
#     def test_get_root(self, request_client):
#         """GET 根路径 — 验证服务可达"""
#         try:
#             resp = request_client.get("/")
#             logger.info(f"GET / -> {resp.status_code}")
#             assert resp.status_code < 500, f"服务器返回错误状态: {resp.status_code}"
#         except Exception as e:
#             pytest.fail(f"请求失败: {e}")


class TestClearVariables:
    """变量清理测试"""

    def test_clear(self):
        """clear_variables 清空类级存储"""
        vm = VariableManager()
        vm.set_variable("temp", "data")
        assert vm.get_variable("temp") == "data"

        VariableManager.clear_variables()
        assert vm.get_variable("temp") is None
