import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryWithCtxMgr(ExhaustiveTestCase):
    """Bug R4-07: ternary 作为 with 上下文管理器（带 as 绑定）— 字节码不一致。

    原始:
        with (ctx_a if cond else ctx_b) as x:
            pass
    缺陷: ternary 作为 with 上下文管理器时，CALL + BEFORE_WITH 在 merge_block
         中消费 ternary 结果，STORE_NAME 消费绑定变量。
         反编译器可能丢失 with 结构或 ternary 结构。
         R3 已识别为已知限制（R3-10），R4 重测以确认 with as 复合上下文。
    """
    SOURCE_CODE = """with (ctx_a if cond else ctx_b) as x:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
