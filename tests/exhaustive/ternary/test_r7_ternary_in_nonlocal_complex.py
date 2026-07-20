import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInNonlocalComplex(ExhaustiveTestCase):
    """Bug R7: nonlocal + ternary + 外层闭包变量 — 字节码不一致。

    原始:
        def f():
            x = 1
            def g():
                nonlocal x
                x = a if c else b
                return x
            g()
            return x
    缺陷: 嵌套函数 nonlocal + ternary 重新赋值 + return，且外层 f
         也 return x。R5 已测 nonlocal + ternary 简单变体
         (test_r5_ternary_in_nonlocal)，R7 在内层 g 增加 return x，
         使 STORE_DEREF + LOAD_DEREF 链与 ternary merge 块的归属关系
         更复杂。
    """
    SOURCE_CODE = """def f():
    x = 1
    def g():
        nonlocal x
        x = a if c else b
        return x
    g()
    return x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
