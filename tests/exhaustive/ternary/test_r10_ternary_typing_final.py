import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryTypingFinal(ExhaustiveTestCase):
    """Bug R10: typing.final + ternary — 字节码不一致。

    原始:
        from typing import final
        @final
        class C:
            x = (a if c else b)
    缺陷: @final class decorator + class body ternary。@final 调用栈帧
         PUSH_NULL + LOAD_NAME final + LOAD_BUILD_CLASS + LOAD_CONST C_code +
         MAKE_FUNCTION + LOAD_CONST 'C' + PRECALL + CALL + PRECALL + CALL +
         STORE_NAME C。class body ternary merge 块的 STORE_NAME x 与
         @final 装饰器调用栈帧可能冲突。依「父引用子入口」：
         @final Call 通过 LOAD_BUILD_CLASS 之后的 CALL 引用 ClassDef；
         class body Assign 通过 STORE_NAME x 引用 ternary 子节点。
    """
    SOURCE_CODE = """from typing import final
@final
class C:
    x = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
