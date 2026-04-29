# AutoApiTest

基于 Python + Pytest + Allure 的 API 自动化测试框架，支持多环境配置、变量传递、数据库连接池和丰富的报告输出。

## 特性

- **多环境配置** — 自动发现环境配置，`--environment` 一键切换
- **变量系统** — 全局变量 + JSONPath 提取 + `$var$` 占位符替换，串联接口依赖
- **Allure 报告** — 历史趋势、环境信息、请求/响应 HTML 附件
- **数据库连接池** — 支持 SQLite / MySQL / PostgreSQL / SQL Server，配置驱动自动适配
- **HTTP 客户端** — 基于 requests.Session + 自动重试，变量替换透明化
- **美化终端输出** — 基于 rich 库，颜色区分信息层级
- **并行执行** — 集成 pytest-xdist

## 项目结构

```
AutoApiTest/
├── setting/                  # 配置包（自动发现环境）
│   ├── __init__.py           # 配置管理器：扫描、加载、属性代理
│   ├── base_config.py        # 基础配置类，定义全部默认值
│   ├── dev_config.py         # 开发环境
│   ├── test_config.py        # 测试环境
│   ├── staging_config.py     # 预发布环境
│   └── prod_config.py        # 生产环境
├── common/                   # 公共模块
│   ├── __init__.py
│   ├── request_client.py     # HTTP 请求客户端（Session + 重试 + 变量替换）
│   ├── variable_manager.py   # 变量管理器（全局存储 + JSONPath 提取）
│   ├── database.py           # 数据库连接池（SQLite/MySQL/PostgreSQL/SQL Server）
│   ├── runner.py             # pytest 命令构建与子进程执行
│   ├── allure_utils.py       # Allure 报告生成/打开/历史趋势
│   ├── console.py            # rich 终端美化输出
│   ├── logger.py             # loguru 日志配置
│   └── tools.py              # 动态变量生成函数（timestamp, random_string）
├── tests/                    # 测试用例
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures 与 hooks
│   └── test_1.py             # 变量存取 / JSONPath 提取用例
├── data/                     # 测试数据文件
├── logs/                     # 日志输出
├── report/                   # 报告输出（gitignore）
│   ├── allure/
│   │   ├── allure-result/    # 原始结果
│   │   ├── allure-html/      # 生成的报告
│   │   └── allure-history/   # 趋势历史备份
│   └── html/                 # pytest-html 报告
├── run_tests.py              # CLI 执行入口
├── pytest.ini                # pytest 配置（markers, 发现规则）
├── requirements.txt
└── pyproject.toml
```

## 快速开始

### 1. 安装

```bash
# Python 3.10+
# 安装 uv（如未安装）：pip install uv

# 同步依赖（自动创建 .venv 并安装所有依赖）
uv sync

# Allure 命令行工具（报告生成需要）
# 将 allure-bat 放到项目根目录，或安装到 PATH
```

### 2. 运行测试

```bash
# 默认环境 (dev)
uv run python run_tests.py

# 指定环境
uv run python run_tests.py --environment test

# 运行并生成 Allure 报告
uv run python run_tests.py --environment test --run-and-report

# 并行执行
uv run python run_tests.py --workers 4

# 生成 HTML 报告
uv run python run_tests.py --html-report

# 仅生成报告（不运行测试）
uv run python run_tests.py --generate-report

# 打开/预览报告
uv run python run_tests.py --open-report
uv run python run_tests.py --review-report

# 直接使用 pytest
uv run pytest tests/ --environment=test
```

### 3. 查看报告

- Allure：`report/allure/allure-html/index.html`
- HTML：`report/html/report.html`
- 日志：`logs/auto_api_test_YYYYMMDD.log`

## 配置系统

### 新增环境

只需创建一个 `setting/xxx_config.py`，会被自动发现和注册：

```python
# setting/uat_config.py
from setting.base_config import BaseConfig

class UatConfig(BaseConfig):
    CURRENT_ENVIRONMENT = 'uat'
    BASE_URL = 'https://uat-api.example.com'
    DESCRIPTION = 'UAT 环境'

    # 按需覆盖任意配置项
    HTTP_CONFIG = {**BaseConfig.HTTP_CONFIG, 'verify_ssl': False}
```

即可通过 `--environment=uat` 使用，无需修改任何现有代码。

### 配置项速览

| 配置段 | 用途 |
|--------|------|
| `CURRENT_ENVIRONMENT` | 环境名（必填） |
| `BASE_URL` | API 基础地址（必填） |
| `LOG_CONFIG` | 日志级别、目录、轮转策略 |
| `HTTP_CONFIG` | 超时、SSL 验证、重试策略、默认请求头 |
| `ALLURE_CONFIG` | 报告开关、路径、环境属性、分类 |
| `RUN_CONFIG` | 并发数、失败停止策略 |
| `VARIABLE_CONFIG` | 占位符模式、全局变量、动态变量 |
| `EMAIL_CONFIG` | 邮件通知 |
| `DATABASE_CONFIG` | 数据库类型、连接参数、连接池大小 |

### 在代码中读取配置

```python
import setting as config

# 直接访问属性
print(config.BASE_URL)
print(config.LOG_CONFIG['log_level'])

# 切换环境
from setting import reload_config
reload_config('prod')
```

## 编写测试

### 可用 Fixtures

| fixture | 作用域 | 说明 |
|---------|--------|------|
| `request_client` | session | HTTP 请求客户端，自动替换变量、记录日志 |
| `variable_manager` | session | 变量管理器，跨用例共享变量 |
| `database` | session | 数据库连接池（需 `DATABASE_CONFIG['enabled']=True`） |

### 示例

```python
import pytest
from common.variable_manager import VariableManager

class TestLogin:
    @pytest.mark.api
    def test_login(self, request_client, variable_manager):
        # 发送登录请求
        resp = request_client.post("/api/login", json_data={
            "username": "admin",
            "password": "123456"
        })
        assert resp.status_code == 200

        # 用 JSONPath 提取 token，存入全局变量
        variable_manager.extract_variables(
            {"token": "$.data.token"},
            resp.json()
        )

    @pytest.mark.api
    def test_profile(self, request_client):
        # URL 和请求头中的 $token$ 会被自动替换
        resp = request_client.get("/api/user/profile")
        assert resp.status_code == 200
```

### 变量系统

```python
# 手动设置
variable_manager.set_variable("uid", "100")

# 从 API 响应提取
variable_manager.extract_variables(
    {"user_id": "$.data.id", "token": "$.data.token"},
    response.json()
)

# 自动替换：URL、请求头、请求体中的 $var$ 占位符
# GET /users/$uid$/profile  →  GET /users/100/profile
# {"Authorization": "Bearer $token$"}  →  {"Authorization": "Bearer abc123"}
```

变量存储为类级别，同一测试会话内所有用例共享。可通过 `VARIABLE_CONFIG['global_variables']` 预设初始值。

### 数据库操作

```python
@pytest.mark.api
def test_query(self, database):
    if database is None:
        pytest.skip("数据库未启用")
    rows = database.query_dict("SELECT * FROM users WHERE status = ?", ("active",))
```

## Allure 报告

框架在 pytest 会话结束时自动写入 `environment.properties`，支持历史趋势。

```python
# ALLURE_CONFIG 结构
ALLURE_CONFIG = {
    'enabled': True,
    'allure_bin': 'allure-bat/bin/allure.bat',  # allure 可执行文件
    'results_dir': 'report/allure/allure-result',
    'report_dir': 'report/allure/allure-html',
    'history_dir': 'report/allure/allure-history',
    'clean_results': True,
    'environment_properties': {'Framework': 'AutoApiTest'},
    'categories': [...],
}
```

报告中自动附加：请求 HTML（方法、URL、Headers、Body）、响应 HTML（状态码、Headers、Body）、cURL 命令。

## 依赖

本项目使用 [uv](https://docs.astral.sh/uv/) 管理依赖，完整依赖列表见 [pyproject.toml](pyproject.toml)。

| 包 | 用途 |
|----|------|
| pytest >= 7.0 | 测试框架 |
| requests >= 2.28 | HTTP 客户端 |
| allure-pytest >= 2.9 | Allure 报告 |
| pytest-html >= 3.2 | HTML 报告 |
| pytest-xdist >= 3.0 | 并行测试 |
| loguru >= 0.7 | 日志 |
| rich >= 13.0 | 终端美化 |
| jsonpath-ng >= 1.6 | JSONPath 解析 |
| DBUtils >= 3.0 | 数据库连接池 |
| openpyxl >= 3.0 | Excel 文件读取 |
| pandas >= 1.5 | 数据处理 |

数据库驱动按需安装：`pymysql`（MySQL）、`psycopg2-binary`（PostgreSQL）、`pymssql`（SQL Server）。

## License

[MIT](LICENSE)
