import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAssertReturnConsumer(ExhaustiveTestCase):
    """Bug R9: assert + return 共享同一 ternary consumer — 字节码不一致。

    原始:
        def f():
            assert (a if c else b)
            return x if c2 else y
    缺陷: R8 已测 multi_same_consumer。R9 测 assert + return 共享
         consumer 变体：两个 ternary 在同一函数体内，第一个 ternary
         merge 块含 LOAD_ASSERTION_ERROR + RAISE_VARARGS（assert 基础
         设施），第二个 ternary merge 块含 RETURN_VALUE，可能暴露
         assert 基础设施过滤与 return ternary 识别的冲突。
    """
    SOURCE_CODE = """def f():
    assert (a if c else b)
    return x if c2 else y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
