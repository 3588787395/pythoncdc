import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryStaticmethodDefault(ExhaustiveTestCase):
    """Bug R10: staticmethod + ternary default arg — 字节码不一致。

    原始:
        class C:
            @staticmethod
            def m(x=(a if c else b)):
                pass
    缺陷: R9-13 已知 abstractmethod + ternary default 失败。R10 测
         staticmethod 变体：@staticmethod 装饰的方法默认参数是 ternary。
         字节码 LOAD_NAME staticmethod + ternary merge + LOAD_CONST code +
         MAKE_FUNCTION + LOAD_CONST defaults + BUILD_TUPLE + PRECALL + CALL
         + STORE_NAME m，ternary merge 块的栈输出作为 default tuple 的元素，
         可能与 @staticmethod 调用栈冲突。依「父引用子入口」：
         @staticmethod Call 通过 MAKE_FUNCTION 之后的 CALL 引用 ternary 子节点。
    """
    SOURCE_CODE = """class C:
    @staticmethod
    def m(x=(a if c else b)):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
