import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryDecoratorChainTernaryArg(ExhaustiveTestCase):
    """Bug R10: decorator chain + ternary arg — 字节码不一致。

    原始:
        @deco1
        @deco2(a if c else b)
        def f():
            pass
    缺陷: R9-14 已知 class decorator arg ternary 失败（@deco(a if c else b)
         丢失装饰器调用）。R10 测 decorator 链变体：两层装饰器中第二层带
         ternary 参数。字节码 LOAD_NAME deco1 + LOAD_NAME deco2 + ternary
         merge + PRECALL + CALL（deco2(arg)）+ LOAD_CONST code + MAKE_FUNCTION
         + PRECALL + CALL（deco2(arg)(f)）+ PRECALL + CALL（deco1(...)(f)）
         + STORE_NAME f，三段 CALL 链与 ternary merge 块归属可能冲突。
         依「父引用子入口」：装饰器链通过 cond_block 入口 + merge_block 的
         CALL 引用 ternary 子节点作为 deco2 参数。
    """
    SOURCE_CODE = """@deco1
@deco2(a if c else b)
def f():
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
