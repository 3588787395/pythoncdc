import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAbcAbstractPropertySetter(ExhaustiveTestCase):
    """Bug R10-08 (re-verify in R11): ABC abstract property + setter + ternary.

    原始:
        from abc import ABC, abstractmethod
        class C(ABC):
            @property
            @abstractmethod
            def x(self):
                ...
            @x.setter
            def x(self, v):
                self._x = (v if c else 0)
    缺陷: @property + @abstractmethod 装饰器栈 + @x.setter + ternary 赋值。
         两层装饰器链 + 类继承 ABC + ternary merge 块的 STORE_ATTR _x，
         可能暴露 decorator chain 重建与 ternary 归属冲突。
    """
    SOURCE_CODE = """from abc import ABC, abstractmethod
class C(ABC):
    @property
    @abstractmethod
    def x(self):
        ...
    @x.setter
    def x(self, v):
        self._x = (v if c else 0)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
