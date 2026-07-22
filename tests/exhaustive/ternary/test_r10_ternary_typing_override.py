import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryTypingOverride(ExhaustiveTestCase):
    """Bug R10: typing.override + ternary (PEP 698) — 字节码不一致。

    原始:
        from typing import override
        class C:
            @override
            def m(self):
                return (a if c else b)
    缺陷: @override 装饰器 + return (ternary) body。@override 调用栈帧
         PUSH_NULL + LOAD_NAME override + LOAD_CONST code + MAKE_FUNCTION
         + PRECALL + CALL + STORE_NAME m。return (ternary) 的 merge 块含
         RETURN_VALUE。R10 测 PEP 698 @override 装饰器变体，验证新装饰器
         与 return ternary merge 块的归属冲突。依「父引用子入口」：
         @override Call 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject；
         return ternary 通过 merge_block 的 RETURN_VALUE 引用 ternary 子节点。
    """
    SOURCE_CODE = """from typing import override
class C:
    @override
    def m(self):
        return (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
