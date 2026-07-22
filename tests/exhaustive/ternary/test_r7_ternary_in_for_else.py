import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInForElse(ExhaustiveTestCase):
    """Bug R7: for-else 块中 ternary 赋值 — 字节码不一致。

    原始:
        for x in ys:
            pass
        else:
            y = a if c else b
    缺陷: for-else 结构中，else 块在循环正常结束（无 break）时执行，
         其中包含 ternary 赋值。期望 else 块中的 ternary 正确归约为
         IfExp 赋值；当前疑似 for-else 的出口块（JUMP_BACKWARD 回到循环头
         vs 跳出到 else）与 ternary entry/merge 块共享导致归属冲突。
    """
    SOURCE_CODE = """for x in ys:
    pass
else:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
