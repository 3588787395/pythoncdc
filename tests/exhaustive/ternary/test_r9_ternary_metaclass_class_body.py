import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryMetaclassClassBody(ExhaustiveTestCase):
    """Bug R9: metaclass class body + ternary 属性 — 字节码不一致。

    原始:
        class C(metaclass=M):
            attr = a if c else b
            def m(self):
                return self.attr
    缺陷: 带 metaclass 关键字的类体中 ternary 赋值。R8 已测 class body
         ternary。R9 测 metaclass 变体：metaclass=M 通过 LOAD_NAME M +
         KWAPPS 0 + BUILD_MAP 1 + CALL 构建 kwargs，与后续 ternary merge
         块的 STORE_NAME attr 在同一 class code object，可能暴露 kwargs
         构建与 ternary 归属的冲突。
    """
    SOURCE_CODE = """class C(metaclass=M):
    attr = a if c else b
    def m(self):
        return self.attr
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
