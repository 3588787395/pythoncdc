import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19WithMultiCtxInIfBody(ExhaustiveTestCase):
    # if body 内含 with 多上下文 + as 绑定 + 嵌套 with：
    # def f(flag):
    #     if flag:
    #         with open('a') as fa, open('b') as fb:
    #             data = fa.read()
    #             with open('c') as fc:
    #                 data += fc.read()
    #             return data + fb.read()
    #     return None
    # 字节码 BEFORE_WITH / WITH / SETUP_WITH / WITH_EXCEPT_START
    # / 反编译器在 if body 内多 with 上下文 + 嵌套 with 时易丢失 as 绑定或嵌套 with。
    SOURCE_CODE = """def f(flag):
    if flag:
        with open('a') as fa, open('b') as fb:
            data = fa.read()
            with open('c') as fc:
                data += fc.read()
            return data + fb.read()
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
