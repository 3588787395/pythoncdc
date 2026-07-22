import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryPartialmethod(ExhaustiveTestCase):
    """Bug R10: functools.partialmethod + ternary — 字节码不一致。

    原始:
        from functools import partialmethod
        class C:
            def _m(self, x):
                return x
            m = partialmethod(_m, (a if c else b))
    缺陷: R9-16 已知 partial(g, ternary) 失败。R10 测 partialmethod 变体：
         partialmethod(_m, ternary) 在 class body 中作为属性赋值。partialmethod
         调用栈帧 LOAD_NAME partialmethod + LOAD_NAME _m + ternary merge +
         PRECALL + CALL + STORE_NAME m。ternary merge 块的栈输出作为
         partialmethod 第二个参数，可能暴露 ternary consumer 识别冲突。
         依「父引用子入口」：父 Assign 通过 STORE_NAME m 引用 partialmethod
         Call 节点，partialmethod Call 通过 cond_block 的 _m 入口 +
         merge_block 的 CALL 引用 ternary 子节点作为第二个参数。
    """
    SOURCE_CODE = """from functools import partialmethod
class C:
    def _m(self, x):
        return x
    m = partialmethod(_m, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
