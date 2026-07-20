import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17ClassMultiInheritInIf(ExhaustiveTestCase):
    # if 体内多继承 class 定义：
    # if c:
    #     class C(A, B):
    #         def m(self):
    #             return 1
    # 字节码 LOAD_NAME A / LOAD_NAME B / BUILD_TUPLE / LOAD_BUILD_CLASS
    # / 反编译器在 if body 内多基类 class 定义时易只保留第一个基类，
    # 或把 BUILD_TUPLE 误归到 __build_class__ 的 kwargs。
    SOURCE_CODE = """if c:
    class C(A, B):
        def m(self):
            return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
