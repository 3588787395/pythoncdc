import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryDecoratorAttrArg(ExhaustiveTestCase):
    """Bug R10: decorator arg 是 attribute ternary — 字节码不一致。

    原始:
        @deco(a.b if c else d.e)
        def f():
            pass
    缺陷: R9-14 已知 class decorator arg ternary 失败。R10 测 attribute
         ternary 变体：ternary 表达式两侧都是 LOAD_ATTR，true_block 与
         false_block 都含 LOAD_NAME + LOAD_ATTR 序列。装饰器调用栈帧
         PUSH_NULL + LOAD_NAME deco + ternary merge + PRECALL + CALL +
         LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL，与 ternary
         merge 块归属可能冲突。依「父引用子入口」：装饰器 Call 通过
         cond_block 的 deco 入口 + merge_block 的 CALL 引用 ternary 子节点。
    """
    SOURCE_CODE = """@deco(a.b if c else d.e)
def f():
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
