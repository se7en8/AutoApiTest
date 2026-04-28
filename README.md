# API 自动化测试框架

基于 Python + Pytest + Allure 的接口自动化测试框架。

## 特性

- 🔗 **接口依赖处理**：支持接口间变量传递，实现复杂业务流测试
- 📈 **Allure 报告**：自动生成美观的测试报告，支持动态标题和特性分类
- 🚀 **Pytest 集成**：利用 pytest 强大的 fixture 和参数化功能
- 🔧 **可扩展架构**：模块化设计，易于扩展和维护
- 📝 **详细日志**：完整的请求/响应日志，便于调试

## 项目结构

```
├── common/           # 公共工具类
│   ├── __init__.py
│   ├── request_client.py # 请求客户端
│   ├── variable_manager.py # 变量管理器
│   ├── test_executor.py # 测试执行器
│   └── logger.py    # 日志配置
├── tests/           # 测试用例
│   ├── __init__.py
│   ├── conftest.py     # pytest 配置
│   └── test_api_template.py # 测试用例模板
├── logs/            # 日志文件
├── config/          # 配置文件
│   └── settings.py  # 项目配置
├── requirements.txt # 依赖包
└── run_tests.py     # 测试执行脚本
```

## 快速开始

### 1. 环境准备

```bash
# 安装 Python 3.10+
python --version

# 安装依赖
pip install -r requirements.txt

# 安装 Allure 命令行工具
# Windows: scoop install allure
# Mac: brew install allure
```

### 2. 编写测试用例

在 `tests/` 目录下编写 Python 测试用例，使用框架提供的 fixture 和工具函数。

### 3. 运行测试

```bash
# 运行所有测试
python run_tests.py

# 使用 pytest 直接运行
pytest tests/ --alluredir=./allure-results

# 生成 Allure 报告
allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report
```

### 4. 查看报告

- Allure 报告：打开 `allure-report/index.html`
- HTML 报告：运行后生成 `report.html`
- 日志文件：查看 `logs/` 目录下的日志

## 配置说明

框架的主要配置在 `config/settings.py` 中：

```python
# 基础配置
BASE_URL = "http://api.example.com"
LOG_LEVEL = "INFO"

# Allure 配置
ALLURE_ENABLE = True
ALLURE_FEATURE = "API 测试"
ALLURE_STORY = "自动化测试"
```

## 扩展指南

### 添加新的工具类
在 `common/` 目录下创建新的 Python 文件，实现相应功能。

### 自定义钩子函数
在 `tests/` 目录下编写钩子函数，通过 `get_hook_function` 查找和调用。

### 自定义断言
修改 `tests/test_api_template.py` 中的断言逻辑，或使用 `common/test_executor.py` 中的断言工具函数。

## 最佳实践

1. **用例设计**：保持用例独立性，合理使用依赖关系
2. **变量管理**：明确变量作用域，避免命名冲突
3. **错误处理**：为关键操作添加异常处理和重试机制
4. **报告优化**：为每个用例设置有意义的 Allure 标题和描述
5. **持续集成**：将框架集成到 CI/CD 流程中

## 常见问题

Q: 变量替换不生效？
A: 检查变量名是否匹配，提取规则是否正确。

Q: Allure 报告没有生成？
A: 确保安装了 allure-pytest 和 Allure 命令行工具。

## 许可证

MIT License
