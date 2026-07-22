import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryDictGetDefault(ExhaustiveTestCase):
    """Bug R12 (new): dict.get(key, default=ternary) — 字节码不一致。

    原始:
        d.get(k, (a if c else b))
    缺陷: ternary 作为 dict.get 的第二个位置参数（default）。merge_block
         末尾的 CALL 2 消费 ternary 结果作为 default。cond_block preload
         含 PUSH_NULL + LOAD_NAME d + LOAD_ATTR get + LOAD_NAME k，ternary
         merge 块的栈输出作为 CALL 第二个 arg。可能暴露 ternary 嵌入 Call
         位置参数的归约冲突（与 kwarg_call 不同：位置 arg 无 KW_NAMES）。
    """
    SOURCE_CODE = """d.get(k, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
