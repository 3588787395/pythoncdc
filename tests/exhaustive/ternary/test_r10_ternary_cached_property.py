import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryCachedProperty(ExhaustiveTestCase):
    """Bug R10: functools.cached_property + ternary in body — 字节码不一致。

    原始:
        from functools import cached_property
        class C:
            @cached_property
            def x(self):
                return (a if c else b)
    缺陷: @cached_property 装饰器 + return (ternary) body。@cached_property
         调用栈帧 PUSH_NULL + LOAD_NAME cached_property + LOAD_CONST code +
         MAKE_FUNCTION + PRECALL + CALL + STORE_NAME x。return (ternary)
         的 merge 块含 RETURN_VALUE。R3 已测 return ternary；R10 测
         @cached_property 装饰器变体，验证 decorator 调用与 return ternary
         merge 块的归属冲突。依「父引用子入口」：@cached_property Call
         通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject；return ternary
         通过 merge_block 的 RETURN_VALUE 引用 ternary 子节点。
    """
    SOURCE_CODE = """from functools import cached_property
class C:
    @cached_property
    def x(self):
        return (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
