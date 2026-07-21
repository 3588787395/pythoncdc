import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernarySetName(ExhaustiveTestCase):
    """Bug R11 (new): __set_name__ + ternary in body.

    原始:
        class Desc:
            def __set_name__(self, owner, name):
                self.name = (name if c else 'default')
        class C:
            x = Desc()
    缺陷: __set_name__ 是 descriptor protocol 隐式方法，在类创建时被调用。
         body 含 ternary 属性赋值。self.name = (name if c else 'default') 的
         ternary merge 块 STORE_ATTR name 与 Desc() 调用栈、LOAD_CONST 'x' +
         STORE_NAME x 共存。__set_name__ code object 内 ternary 区域归约。
    """
    SOURCE_CODE = """class Desc:
    def __set_name__(self, owner, name):
        self.name = (name if c else 'default')
class C:
    x = Desc()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
