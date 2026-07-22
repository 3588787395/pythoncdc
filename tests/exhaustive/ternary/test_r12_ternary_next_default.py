import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryNextDefault(ExhaustiveTestCase):
    """Bug R12 (new): next(iterator, default=ternary) — 字节码不一致。

    原始:
        next(it, (a if c else b))
    缺陷: ternary 作为 next() 的第二个位置参数（default）。CALL 2 消费
         ternary merge 块的栈输出。next 是 builtin，LOAD_GLOBAL next
         带 PUSH_NULL (arg&1=1)。可能暴露 builtin 调用 + ternary 位置参数
         的归约路径与 dict.get 不同（dict.get 走 LOAD_ATTR 路径）。
    """
    SOURCE_CODE = """next(it, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
