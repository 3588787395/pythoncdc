import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInImportFromAlias(ExhaustiveTestCase):
    """Bug R8: import from 后紧跟 ternary 赋值 — 字节码不一致。

    原始:
        from x import y as z
        w = a if c else b
    缺陷: import from 后紧跟 ternary 赋值。R7 已测过 import_test。
         R8 测 import from with as alias 变体：IMPORT_NAME +
         IMPORT_FROM + STORE_NAME z 的栈帧与后续 ternary merge 块的
         STORE_NAME w 可能共享 entry 块导致归属冲突。
    """
    SOURCE_CODE = """from x import y as z
w = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
