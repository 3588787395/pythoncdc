import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryDataclassDefaultFactory(ExhaustiveTestCase):
    """Bug R10-06 (re-verify in R11): dataclass default_factory lambda ternary.

    原始:
        from dataclasses import dataclass, field
        @dataclass
        class C:
            x: int = field(default_factory=lambda: (a if c else b))
    缺陷: ternary 在 lambda code object 内（独立区域），field(default_factory=...)
         调用栈帧 PUSH_NULL + LOAD_NAME field + LOAD_CONST lambda_code +
         MAKE_FUNCTION + KW_NAMES + LOAD_CONST default_factory + PRECALL + CALL +
         STORE_NAME x 与 AnnAssign 的 value 表达式归属可能冲突。
    """
    SOURCE_CODE = """from dataclasses import dataclass, field
@dataclass
class C:
    x: int = field(default_factory=lambda: (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
