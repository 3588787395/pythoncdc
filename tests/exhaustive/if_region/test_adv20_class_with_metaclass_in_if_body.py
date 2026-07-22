import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20ClassWithMetaclassInIfBody(ExhaustiveTestCase):
    # if body 内含 class 定义 + metaclass 关键字参数 + 方法：
    # def f(flag):
    #     if flag:
    #         class Meta(type):
    #             pass
    #         class C(metaclass=Meta):
    #             def __init__(self, x):
    #                 self.x = x
    #             def get(self):
    #                 return self.x
    #         return C(10).get()
    #     return 0
    # 字节码 LOAD_BUILD_CLASS / LOAD_CONST 'metaclass' / CALL kw
    # / 反编译器在 if body 内 class 含 metaclass= 关键字时易丢失 metaclass 参数。
    SOURCE_CODE = """def f(flag):
    if flag:
        class Meta(type):
            pass
        class C(metaclass=Meta):
            def __init__(self, x):
                self.x = x
            def get(self):
                return self.x
        return C(10).get()
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
