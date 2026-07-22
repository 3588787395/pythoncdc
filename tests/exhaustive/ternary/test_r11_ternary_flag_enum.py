import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryFlagEnum(ExhaustiveTestCase):
    """Bug R11 (new): Flag enum + ternary in member value.

    原始:
        from enum import Flag, auto
        class Perm(Flag):
            R = (auto() if c else 1)
            W = (auto() if c2 else 2)
            X = (auto() if c3 else 4)
    缺陷: Flag 枚举的成员值通过 auto() + ternary 选择，三个 ternary 共存
         于同一 class code object。auto() 在 cond_block 的 preload 中（CALL），
         ternary merge 块的 STORE_NAME R/W/X 与 Flag 元类调用栈 PUSH_NULL +
         LOAD_NAME Flag + PUSH_NULL + LOAD_BUILD_CLASS + LOAD_CONST Perm_code +
         MAKE_FUNCTION + LOAD_CONST 'Perm' + PRECALL + CALL + PRECALL + CALL +
         STORE_NAME Perm 共存。
    """
    SOURCE_CODE = """from enum import Flag, auto
class Perm(Flag):
    R = (auto() if c else 1)
    W = (auto() if c2 else 2)
    X = (auto() if c3 else 4)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
