import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryAugAssignSubscrCall(ExhaustiveTestCase):
    """Bug R13 (new): x[0] += f(a if c else b) — aug assign subscr + call arg ternary。

    原始:
        x[0] += f(a if c else b)
    缺陷: ternary 作为 aug assign subscr 右值 f() 的位置参数。target x[0]
         复制模板 LOAD x + LOAD_CONST 0 + BINARY_SUBSCR + COPY 2 + COPY 1 +
         LOAD_GLOBAL f + ternary merge + PRECALL + CALL 1 + BINARY_OP(+=) +
         STORE_SUBSCR。R8 已测 aug_assign_subscr 单纯场景（无 call），R12 测
         aug_assign_attr。R13 测 aug_assign_subscr + call arg ternary 复合场景。
    """
    SOURCE_CODE = """x[0] += f(a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
