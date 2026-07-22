import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19NonlocalWithNestedFuncInIfBody(ExhaustiveTestCase):
    # 外层函数 + if body 内含 nonlocal + nested def + 嵌套调用：
    # def outer():
    #     count = 0
    #     def f(flag):
    #         if flag:
    #             nonlocal count
    #             count += 1
    #             def helper():
    #                 return count * 2
    #             return helper()
    #         return count
    #     return f
    # 字节码 LOAD_DEREF / STORE_DEREF / MAKE_FUNCTION / LOAD_CLOSURE
    # / 反编译器在 if body 内 nonlocal + nested def + closure 时易丢失 nonlocal 或 nested def。
    SOURCE_CODE = """def outer():
    count = 0
    def f(flag):
        if flag:
            nonlocal count
            count += 1
            def helper():
                return count * 2
            return helper()
        return count
    return f"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
