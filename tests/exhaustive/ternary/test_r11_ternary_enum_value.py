import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryEnumValue(ExhaustiveTestCase):
    """Bug R11 (new): Enum with ternary value.

    原始:
        from enum import Enum
        class Color(Enum):
            RED = (1 if c else 2)
            GREEN = (3 if c2 else 4)
    缺陷: Enum 子类中两个成员值都是 ternary。enum 元类 Enum.__init__ 在
         类创建后处理成员。类体内两个 ternary merge 块的 STORE_NAME RED/GREEN
         共存于同一 class code object。enum 的 LOAD_NAME Enum 在
         __build_class__ args 中。依「自底向上归约」：每个 ternary 在 class
         code object 内独立归约；依「每块唯一归属」：两个 ternary 各自的
         merge 块归属各自的 AnnAssign/Assign 表达式。
    """
    SOURCE_CODE = """from enum import Enum
class Color(Enum):
    RED = (1 if c else 2)
    GREEN = (3 if c2 else 4)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
