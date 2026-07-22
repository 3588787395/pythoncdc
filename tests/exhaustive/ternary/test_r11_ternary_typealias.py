import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypeAlias(ExhaustiveTestCase):
    """Bug R11 (new): typing.TypeAlias (PEP 613) + ternary value.

    原始:
        from typing import TypeAlias
        MyType: TypeAlias = (int if c else str)
    缺陷: PEP 613 显式类型别名 TypeAlias 注解 + ternary 右值。AnnAssign
         的 annotation 是 Name('TypeAlias')，value 是 ternary。依「父引用子入口」：
         父 AnnAssign 通过 STORE_NAME MyType 引用 ternary 子节点作为 value。
    """
    SOURCE_CODE = """from typing import TypeAlias
MyType: TypeAlias = (int if c else str)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
