"""
动态变量生成工具函数
config.py 中 auto_generated_variables 指定的函数名必须在此定义
VariableManager 初始化时会自动导入并调用
"""
import time
import random
import string


def generate_timestamp():
    """生成当前 Unix 时间戳"""
    return int(time.time())


def generate_random_string():
    """生成 8 位随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
