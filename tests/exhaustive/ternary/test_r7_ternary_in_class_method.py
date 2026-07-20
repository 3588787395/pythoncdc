import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInClassMethod(ExhaustiveTestCase):
    """Bug R7: 类方法 return ternary — 字节码不一致。

    原始:
        class C:
            def m(self):
                return self.x if c else self.y
    缺陷: 类方法中 return ternary。R3 已测嵌套函数 return ternary
         (test_r3_ternary_nested_func)，R7 测类方法上下文：
         类 code object 内部嵌套方法 code object，方法 LOAD_FAST self
         + LOAD_ATTR x/y 与 ternary merge 块的归属交互。期望 ternary
         正确归约为 Return(IfExp)；当前疑似类方法 code object 边界
         与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """class C:
    def m(self):
        return self.x if c else self.y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
