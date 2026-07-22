import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryWithCtxManager(ExhaustiveTestCase):
    """Bug R3-10: ternary 作为 with 的上下文管理器 — 字节码不一致。

    原始:
        with (ctx_a if cond else ctx_b) as x:
            pass
    缺陷: ternary 作为 with 上下文管理器时，CALL + BEFORE_WITH 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 with 结构或 ternary 结构。
    """
    SOURCE_CODE = """with (ctx_a if cond else ctx_b) as x:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
