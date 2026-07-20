import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInGlobal(ExhaustiveTestCase):
    """Bug R5-10: ternary 在 global 声明后赋值 + 函数内读取 — 字节码不一致。

    原始:
        def f():
            global x
            x = a if c else b
            return x
    缺陷: R3 已通过简单 global + ternary 场景（test_r3_ternary_global）。
         R5 在 global + ternary 赋值后增加 return 语句读取该全局变量。
         期望：STORE_GLOBAL + IfExp 正确归约；当前疑似 IfExp 结构丢失。
    """
    SOURCE_CODE = """def f():
    global x
    x = a if c else b
    return x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
