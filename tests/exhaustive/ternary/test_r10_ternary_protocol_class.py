import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryProtocolClass(ExhaustiveTestCase):
    """Bug R10: Protocol class + ternary — 字节码不一致。

    原始:
        from typing import Protocol
        class MyProto(Protocol):
            x: int = (a if c else b)
    缺陷: Protocol 类中字段带 ternary 默认值。Protocol 基类作为 LOAD_NAME
         Protocol 在 class kwargs 中，与类体 AnnAssign ternary merge 块的
         STORE_NAME x 共存于同一 class code object。R9 已测 metaclass
         class body ternary；R10 测 Protocol 变体。依「父引用子入口」：
         父 AnnAssign 通过 STORE_NAME x 引用 ternary 子节点作为 value。
    """
    SOURCE_CODE = """from typing import Protocol
class MyProto(Protocol):
    x: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
