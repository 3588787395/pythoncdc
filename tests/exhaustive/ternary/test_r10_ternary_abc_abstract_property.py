import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryAbcAbstractProperty(ExhaustiveTestCase):
    """Bug R10: ABC abstract property + ternary — 字节码不一致。

    原始:
        from abc import ABC, abstractmethod
        class C(ABC):
            @property
            @abstractmethod
            def x(self):
                ...
            @x.setter
            def x(self, v):
                self._x = v if c else 0
    缺陷: R9-12 已知 property + setter + double ternary 失败。R10 测 ABC
         + abstract property + setter + ternary 变体：组合 @property +
         @abstractmethod 装饰器栈 + @x.setter + ternary 赋值。两层装饰器
         链 + 类继承 ABC + ternary merge 块的 STORE_ATTR _x，可能暴露
         decorator chain 重建与 ternary 归属的冲突。依「父引用子入口」：
         每个 decorator Call 通过 MAKE_FUNCTION 之后的 CALL 引用下层
         FunctionObject 子节点。
    """
    SOURCE_CODE = """from abc import ABC, abstractmethod
class C(ABC):
    @property
    @abstractmethod
    def x(self):
        ...
    @x.setter
    def x(self, v):
        self._x = v if c else 0
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
