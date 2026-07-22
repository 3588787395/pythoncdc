import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20ClassWithSlotsInIfBody(ExhaustiveTestCase):
    # if body 内含 class 定义 + __slots__ + 多方法 + classmethod + staticmethod：
    # def f(flag):
    #     if flag:
    #         class Point:
    #             __slots__ = ('x', 'y')
    #             def __init__(self, x, y):
    #                 self.x = x
    #                 self.y = y
    #             @classmethod
    #             def origin(cls):
    #                 return cls(0, 0)
    #             @staticmethod
    #             def distance(p1, p2):
    #                 return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    #         return Point.distance(Point(1, 2), Point.origin())
    #     return 0.0
    # 字节码 LOAD_BUILD_CLASS / MAKE_FUNCTION / LOAD_NAME classmethod/staticmethod
    # / 反编译器在 if body 内 class + __slots__ + 多装饰器时易丢失装饰器或 __slots__。
    SOURCE_CODE = """def f(flag):
    if flag:
        class Point:
            __slots__ = ('x', 'y')
            def __init__(self, x, y):
                self.x = x
                self.y = y
            @classmethod
            def origin(cls):
                return cls(0, 0)
            @staticmethod
            def distance(p1, p2):
                return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        return Point.distance(Point(1, 2), Point.origin())
    return 0.0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
