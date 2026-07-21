import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryMultiAbstractmethod(ExhaustiveTestCase):
    """Bug R10: 多个 abstractmethod + ternary default — 字节码不一致。

    原始:
        class C:
            @abstractmethod
            def m1(self, x=(a if c else b)):
                pass
            @abstractmethod
            def m2(self, y=(d if e else f)):
                pass
    缺陷: R9-13 已知单 abstractmethod + ternary default 失败。R10 测多个
         abstractmethod 变体：两个 ternary 在 class body 外层 code object
         计算，分别用于 m1 和 m2 的 default tuple。两个 ternary 区域 +
         两次 @abstractmethod 调用栈帧 + 两次 MAKE_FUNCTION + BUILD_TUPLE
         序列在同一 class code object，可能暴露 ternary 归属与多次装饰器
         调用的冲突。依「父引用子入口」：每个 @abstractmethod Call 通过
         其 MAKE_FUNCTION 之后的 CALL 引用对应 ternary 子节点。
    """
    SOURCE_CODE = """class C:
    @abstractmethod
    def m1(self, x=(a if c else b)):
        pass
    @abstractmethod
    def m2(self, y=(d if e else f)):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
