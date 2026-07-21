import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryClassmethodDefault(ExhaustiveTestCase):
    """Bug R10: classmethod + ternary default arg — 字节码不一致。

    原始:
        class C:
            @classmethod
            def m(cls, x=(a if c else b)):
                pass
    缺陷: R9-13 已知 abstractmethod + ternary default 失败（装饰器调用
         丢失）。R10 测 classmethod 变体：@classmethod 装饰的方法默认参数
         是 ternary。ternary 在外层 code object 计算（默认参数在函数定义
         时求值），MAKE_FUNCTION + LOAD_CONST defaults + BUILD_TUPLE 与
         PRECALL + CALL（@classmethod 调用）的栈顺序可能冲突。
         依「父引用子入口」：@classmethod Call 通过 MAKE_FUNCTION 之后的
         CALL 引用 ternary 子节点作为 default tuple 的元素。
    """
    SOURCE_CODE = """class C:
    @classmethod
    def m(cls, x=(a if c else b)):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
