import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19DelMultiInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 del 多目标 + 属性 + subscr 混合：
    # def f(flag, obj, d):
    #     if flag:
    #         del obj.attr, d['key'], obj.nested
    #         return 'del_done'
    #     elif flag is None:
    #         del d['a'], d['b'], d['c']
    #         return 'del_keys'
    #     else:
    #         del obj.x, obj.y
    #         return 'del_attrs'
    # 字节码 DELETE_ATTR / DELETE_SUBSCR / DELETE_NAME
    # / 反编译器在 if-elif-else 三分支都含多目标 del 时易结构错乱。
    SOURCE_CODE = """def f(flag, obj, d):
    if flag:
        del obj.attr, d['key'], obj.nested
        return 'del_done'
    elif flag is None:
        del d['a'], d['b'], d['c']
        return 'del_keys'
    else:
        del obj.x, obj.y
        return 'del_attrs'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
