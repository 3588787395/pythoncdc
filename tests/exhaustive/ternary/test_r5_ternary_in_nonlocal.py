import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInNonlocal(ExhaustiveTestCase):
    """Bug R5-11: 嵌套函数中 nonlocal + ternary 赋值 — 字节码不一致。

    原始:
        def outer():
            x = 0
            def inner():
                nonlocal x
                x = a if c else b
            inner()
            return x
    缺陷: nonlocal 声明后 STORE_NAME 改为 STORE_DEREF，merge_block 中
         STORE_DEREF 消费 ternary 结果。反编译器可能误识别 merge_context
         （STORE_DEREF 不在 _try_build_ternary_store_assign 的识别列表中）。
         期望：nonlocal + ternary 正确归约为 IfExp 赋值。
    """
    SOURCE_CODE = """def outer():
    x = 0
    def inner():
        nonlocal x
        x = a if c else b
    inner()
    return x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
