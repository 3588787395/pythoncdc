import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryTypedDictDefault(ExhaustiveTestCase):
    """Bug R10: TypedDict + ternary default — 字节码不一致。

    原始:
        from typing import TypedDict
        class Movie(TypedDict):
            title: str
            year: int = (a if c else b)
    缺陷: TypedDict 类中字段带 ternary 默认值（AnnAssign 的 value 是
         ternary）。TypedDict 基类作为 LOAD_NAME TypedDict 在 class
         kwargs 中，与类体 AnnAssign ternary merge 块的 STORE_NAME year
         共存于同一 class code object。R8 已测 AnnAssign ternary；
         R10 测 TypedDict + AnnAssign + ternary 变体。依「父引用子入口」：
         父 AnnAssign 通过 STORE_NAME year 引用 ternary 子节点作为 value。
    """
    SOURCE_CODE = """from typing import TypedDict
class Movie(TypedDict):
    title: str
    year: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
