import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20DelSliceInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 del slice + del multi-subscr + del attr 组合：
    # def f(flag, lst, obj, d):
    #     if flag == 'a':
    #         del lst[1:3]
    #         del lst[::2]
    #         return lst
    #     elif flag == 'b':
    #         del obj.attr, obj.nested
    #         del d['key1']
    #         return obj
    #     else:
    #         del lst[1], lst[2], lst[3]
    #         del d['k1'], d['k2']
    #         return lst, d
    # 字节码 DELETE_SUBSCR / DELETE_ATTR / BUILD_SLICE
    # / 反编译器在 if-elif-else 三分支都含 del slice/attr/subscr 时易结构错乱。
    SOURCE_CODE = """def f(flag, lst, obj, d):
    if flag == 'a':
        del lst[1:3]
        del lst[::2]
        return lst
    elif flag == 'b':
        del obj.attr, obj.nested
        del d['key1']
        return obj
    else:
        del lst[1], lst[2], lst[3]
        del d['k1'], d['k2']
        return lst, d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
