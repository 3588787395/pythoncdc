import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryFrozenDataclassDefault(ExhaustiveTestCase):
    """Bug R9: frozen dataclass field 默认值 ternary — 字节码不一致。

    原始:
        from dataclasses import dataclass
        @dataclass(frozen=True)
        class C:
            x: int = (a if c else b)
    缺陷: frozen dataclass 的字段默认值是 ternary。dataclass 装饰器
         + 类体内 AnnAssign 的 value 是 ternary，ternary merge 块的
         STORE_NAME x 与 dataclass 装饰器栈、LOAD_NAME dataclass +
         KWAPPS + CALL 的栈顺序可能冲突。
    """
    SOURCE_CODE = """from dataclasses import dataclass
@dataclass(frozen=True)
class C:
    x: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
