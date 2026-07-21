import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryExitStack(ExhaustiveTestCase):
    """Bug R10: contextlib.ExitStack + ternary — 字节码不一致。

    原始:
        from contextlib import ExitStack
        with ExitStack() as stack:
            x = stack.enter_context((a if c else b))
    缺陷: with as stack + ternary as method call arg。ternary merge 块的
         栈输出作为 stack.enter_context() 的参数。with body 字节码
         BEFORE_WITH + LOAD_NAME ExitStack + PRECALL + CALL + SETUP_WITH +
         STORE_NAME stack + ternary merge + LOAD_ATTR enter_context +
         PRECALL + CALL + STORE_NAME x + WITH_CLEANUP，多段 CALL 与 ternary
         merge 块归属可能冲突。依「父引用子入口」：父 Assign 通过
         STORE_NAME x 引用 stack.enter_context Call 节点；enter_context Call
         通过 cond_block 的 stack 入口 + merge_block 的 CALL 引用 ternary 子节点。
    """
    SOURCE_CODE = """from contextlib import ExitStack
with ExitStack() as stack:
    x = stack.enter_context((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
