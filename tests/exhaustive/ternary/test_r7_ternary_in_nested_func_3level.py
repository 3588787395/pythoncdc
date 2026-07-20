import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInNestedFunc3Level(ExhaustiveTestCase):
    """Bug R7: 3 层嵌套函数 return ternary — 字节码不一致。

    原始:
        def f():
            def g():
                def h():
                    return a if c else b
                return h
            return g
    缺陷: 3 层嵌套函数最内层 return ternary。R3 已测 2 层嵌套
         (test_r3_ternary_nested_func)，R6 已测 2 层闭包捕获
         (test_r6_ternary_closure_capture)。R7 测 3 层嵌套：
         3 层 code object 嵌套，最内层 ternary 的归约需要穿越 2 层
         code object 边界。期望 ternary 正确归约；当前疑似多层
         code object 嵌套时内层 ternary 的 region 识别遗漏。
    """
    SOURCE_CODE = """def f():
    def g():
        def h():
            return a if c else b
        return h
    return g
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
