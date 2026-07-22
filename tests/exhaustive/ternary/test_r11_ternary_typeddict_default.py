import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypedDictDefault(ExhaustiveTestCase):
    """Bug R10-07 (re-verify in R11): TypedDict + ternary default.

    原始:
        from typing import TypedDict
        class Movie(TypedDict):
            title: str
            year: int = (a if c else b)
    缺陷: TypedDict 类中字段带 ternary 默认值。TypedDict 基类作为 LOAD_NAME
         TypedDict 在 class kwargs 中，与类体 AnnAssign ternary merge 块的
         STORE_NAME year 共存于同一 class code object。
    """
    SOURCE_CODE = """from typing import TypedDict
class Movie(TypedDict):
    title: str
    year: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
