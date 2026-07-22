import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryEnumClass(ExhaustiveTestCase):
    """Bug R10: enum class + ternary value — 字节码不一致。

    原始:
        from enum import Enum
        class Color(Enum):
            RED = (a if c else b)
            GREEN = 2
    缺陷: enum class 中 enum 字段值是 ternary。Enum 基类作为 LOAD_NAME Enum
         在 class kwargs 中，与类体 ternary 赋值共存于同一 class code object。
         enum 字段 LOAD_NAME a / LOAD_NAME b + ternary merge + STORE_NAME RED
         可能与 Enum 基类加载的栈帧顺序冲突。依「父引用子入口」：
         父 Assign 通过 STORE_NAME RED 引用 ternary 子节点作为右值。
    """
    SOURCE_CODE = """from enum import Enum
class Color(Enum):
    RED = (a if c else b)
    GREEN = 2
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
