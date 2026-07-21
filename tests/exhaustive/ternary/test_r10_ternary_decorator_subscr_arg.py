import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryDecoratorSubscriptArg(ExhaustiveTestCase):
    """Bug R10: decorator arg 是 subscript ternary — 字节码不一致。

    原始:
        @deco(a[b if c else d])
        def f():
            pass
    缺陷: R9-14 已知 class decorator arg ternary 失败。R10 测嵌套
         subscript ternary 变体：ternary 表达式作为 BINARY_SUBSCR 的下标，
         装饰器调用 LOAD_NAME deco + LOAD_NAME a + ternary merge +
         BINARY_SUBSCR + PRECALL + CALL + LOAD_CONST code + MAKE_FUNCTION
         + PRECALL + CALL，ternary merge 后还要 BINARY_SUBSCR 求值，可能
         暴露 ternary merge 块与 BINARY_SUBSCR 的归属冲突。
         依「父引用子入口」：装饰器 Call 通过 cond_block 的 deco 入口
         + merge_block 的 BINARY_SUBSCR 引用 ternary 子节点作为下标。
    """
    SOURCE_CODE = """@deco(a[b if c else d])
def f():
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
