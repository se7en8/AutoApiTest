import allure
import pytest
from common.logger import logger

@allure.feature("API 测试")
@pytest.mark.smoke
def test_api(request_client):
    """
    冒烟测试：检查 API 基本可用性
    """
    # 这里可以添加基本的健康检查
    # 例如：检查首页、健康检查端点等
    logger.info("执行冒烟测试")

    # 示例：检查根端点
    try:
        response = request_client.get('https://uapis.cn/api/v1/misc/hotboard?type=bilibili')
        assert response.status_code < 500, f"服务器错误: {response.status_code}"
        logger.info("冒烟测试通过")
    except Exception as e:
        pytest.fail(f"冒烟测试失败: {e}")