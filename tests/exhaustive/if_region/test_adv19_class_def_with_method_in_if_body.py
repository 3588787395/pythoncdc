import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19ClassDefWithMethodInIfBody(ExhaustiveTestCase):
    # if body 内含 class 定义（带 __init__ 和实例方法）：
    # def f(flag):
    #     if flag:
    #         class Helper:
    #             def __init__(self, val):
    #                 self.val = val
    #             def double(self):
    #                 return self.val * 2
    #         return Helper(10).double()
    #     return 0
    # 字节码 LOAD_BUILD_CLASS / MAKE_FUNCTION / STORE_NAME + CALL
    # / 反编译器在 if body 内嵌套 class def + 方法时易丢失方法或 self 属性。
    SOURCE_CODE = """def f(flag):
    if flag:
        class Helper:
            def __init__(self, val):
                self.val = val
            def double(self):
                return self.val * 2
        return Helper(10).double()
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
