import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryGlobalAssign(ExhaustiveTestCase):
    """Bug R3-15: ternary 在 global 声明后赋值 — 字节码不一致。

    原始:
        def f():
            global x
            x = a if cond else b
    缺陷: global 声明后 STORE_NAME 改为 STORE_GLOBAL，merge_block 中
         STORE_GLOBAL 消费 ternary 结果。
         反编译器可能误识别 merge_context。
    """
    SOURCE_CODE = """def f():
    global x
    x = a if cond else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
