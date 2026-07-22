import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryFrozenDataclassDefault(ExhaustiveTestCase):
    """Bug R9-10 (re-verify in R11): frozen dataclass field default ternary.

    原始:
        from dataclasses import dataclass
        @dataclass(frozen=True)
        class C:
            x: int = (a if c else b)
    缺陷: frozen dataclass 的字段默认值是 ternary。dataclass 装饰器 + 类体
         内 AnnAssign 的 value 是 ternary，merge 块的 STORE_NAME x 与
         dataclass 装饰器栈、KWAPPS + CALL 的栈顺序冲突。
    """
    SOURCE_CODE = """from dataclasses import dataclass
@dataclass(frozen=True)
class C:
    x: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
