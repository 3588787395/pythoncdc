import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryMetaclassNew(ExhaustiveTestCase):
    """Bug R11 (new): metaclass __new__ + ternary.

    原始:
        class Meta(type):
            def __new__(mcs, name, bases, ns):
                cls = super().__new__(mcs, name, bases, ns)
                cls.tag = (a if c else b)
                return cls
        class C(metaclass=Meta):
            pass
    缺陷: metaclass __new__ body 内 ternary 属性赋值 + super() no-arg 调用。
         __new__ 的 code object 内 super().__new__(mcs, name, bases, ns) 的
         CALL + ternary merge 块 STORE_ATTR tag + RETURN_VALUE cls。可能暴露
         super() no-arg 重建（LOAD_GLOBAL super + CALL 0 + LOAD_ATTR __new__）
         与 ternary 归属的冲突。
    """
    SOURCE_CODE = """class Meta(type):
    def __new__(mcs, name, bases, ns):
        cls = super().__new__(mcs, name, bases, ns)
        cls.tag = (a if c else b)
        return cls
class C(metaclass=Meta):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
