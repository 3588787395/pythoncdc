import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryDataclassInitOverride(ExhaustiveTestCase):
    """Bug R11 (new): dataclass with explicit __init__ override + ternary.

    原始:
        from dataclasses import dataclass
        @dataclass
        class C:
            x: int
            def __init__(self, x):
                self.x = (x if c else 0)
    缺陷: dataclass 自动生成 __init__ 被显式覆盖，覆盖的 __init__ 内含 ternary
         赋值。dataclass 装饰器栈 PUSH_NULL + LOAD_NAME dataclass + PUSH_NULL +
         LOAD_BUILD_CLASS + LOAD_CONST C_code + MAKE_FUNCTION + LOAD_CONST 'C' +
         PRECALL + CALL + PRECALL + CALL + STORE_NAME C 与 __init__ 的
         MAKE_FUNCTION + STORE_NAME __init__ 在同一 class code object。__init__
         内 ternary merge 块的 STORE_ATTR self.x 与 return None 隐式结尾。
    """
    SOURCE_CODE = """from dataclasses import dataclass
@dataclass
class C:
    x: int
    def __init__(self, x):
        self.x = (x if c else 0)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
