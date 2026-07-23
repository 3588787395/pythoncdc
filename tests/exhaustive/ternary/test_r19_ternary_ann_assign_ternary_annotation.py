import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryAnnAssignTernaryAnnotation(ExhaustiveTestCase):
    """Bug R19-08: x: (A if c else B) = None — ternary 作 annotated assignment 的注解表达式。

    原始:
        x: (A if c else B) = None
    缺陷: annotated assignment `x: annotation = value` 的 annotation 是 ternary。
         R8 ann_assign 测过 `x: int = (ternary)` (注解是常量 int，value 是 ternary)，
         R6 annotation 测过 `x: (ternary)` (无 value 的纯注解)。本用例 annotation
         是 ternary 且 value 是 None：SETUP_ANNOTATIONS + STORE_NAME x + LOAD_CONST None
         + ternary merge + LOAD_CONST 'x' + STORE_SUBSCR (写入 __annotations__)，
         反编译退化为 `x = None` + `__annotations__['x'] = (A if c else B)` 两段
         独立语句，丢失 SETUP_ANNOTATIONS 指令，字节码指令数不匹配 (12 vs 11)。
    """
    SOURCE_CODE = """x: (A if c else B) = None
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
