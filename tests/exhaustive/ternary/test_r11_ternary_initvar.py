import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryInitVar(ExhaustiveTestCase):
    """Bug R11 (new): dataclass InitVar + ternary default.

    原始:
        from dataclasses import dataclass, InitVar
        @dataclass
        class C:
            x: InitVar[int] = (a if c else b)
            def __post_init__(self, x):
                pass
    缺陷: InitVar 字段默认值是 ternary。InitVar 在 dataclass 中表示该字段
         只传给 __init__ / __post_init__，不存为实例属性。AnnAssign 的
         annotation 是 Subscript(Name('InitVar'), Name('int'))，value 是 ternary。
         ternary merge 块的 STORE_NAME x 与 __post_init__ 的 MAKE_FUNCTION
         在同一 class code object，可能暴露 InitVar annotation 重建与 ternary
         归属的冲突。
    """
    SOURCE_CODE = """from dataclasses import dataclass, InitVar
@dataclass
class C:
    x: InitVar[int] = (a if c else b)
    def __post_init__(self, x):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
