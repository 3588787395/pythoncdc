import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryStarredAssign(ExhaustiveTestCase):
    """Bug R13 (new): x, *y = (a if c else b) — starred assignment ternary。

    原始:
        x, *y = (a if c else b)
    缺陷: ternary 作为 starred assignment 的右值。右值需可迭代，左值包含
         starred target *y。UNPACK_EX 1 在 ternary merge 之后，STORE_NAME x +
         STORE_NAME y。验证 ternary 在 unpack_ex（含 starred target）路径的归约。
    """
    SOURCE_CODE = """x, *y = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
