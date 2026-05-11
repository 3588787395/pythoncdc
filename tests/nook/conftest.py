"""
Nook测试配置 - 提供公共fixture和辅助函数
"""
import pytest
import sys
import os
from pathlib import Path

# 确保项目根目录在sys.path中
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture
def build_cfg_from_source():
    """
    从源代码构建CFG的fixture
    
    使用方法:
        def test_something(build_cfg_from_source):
            cfg = build_cfg_from_source(source_code)
    """
    from core.cfg import build_cfg
    
    def _builder(source: str, func_name: str = None):
        code_obj = compile(source, '<string>', 'exec')
        return build_cfg(code_obj)
    
    return _builder


@pytest.fixture
def generate_ast_from_cfg():
    """
    从CFG生成AST的fixture
    
    使用方法:
        def test_something(generate_ast_from_cfg):
            ast_dict = generate_ast_from_cfg(cfg)
    """
    from core.cfg import generate_ast
    return generate_ast


@pytest.fixture
def sample_function_source():
    """示例源代码fixture"""
    return '''
def test_function(x):
    if x > 0:
        result = "positive"
    else:
        result = "non-positive"
    return result
'''


@pytest.fixture
def sample_loop_source():
    """循环示例源代码fixture"""
    return '''
def test_loop(n):
    result = 0
    for i in range(n):
        result += i
    return result
'''


@pytest.fixture
def sample_try_except_source():
    """try-except示例源代码fixture"""
    return '''
def test_try_except(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    return result
'''
