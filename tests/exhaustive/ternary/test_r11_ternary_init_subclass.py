import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryInitSubclass(ExhaustiveTestCase):
    """Bug R11 (new): __init_subclass__ + ternary in class body.

    原始:
        class Base:
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.tag = (a if c else b)
        class Sub(Base):
            pass
    缺陷: __init_subclass__ 是隐式 classmethod，body 含 ternary 属性赋值。
         cls.tag = (a if c else b) 的 ternary merge 块 STORE_ATTR tag 与
         super().__init_subclass__(**kwargs) 的 CALL_FUNCTION_EX 共存于
         __init_subclass__ code object。可能暴露 super() no-arg 重建 +
         ternary 归属的冲突。
    """
    SOURCE_CODE = """class Base:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.tag = (a if c else b)
class Sub(Base):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
