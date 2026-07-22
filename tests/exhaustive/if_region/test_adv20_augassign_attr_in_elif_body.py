import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20AugassignAttrInElifBody(ExhaustiveTestCase):
    # if-elif-else 三分支各自含对属性的多重 augassign：
    # def f(flag, obj):
    #     if flag == 'a':
    #         obj.x += 1
    #         obj.y *= 2
    #         return obj.x + obj.y
    #     elif flag == 'b':
    #         obj.x -= 1
    #         obj.z **= 3
    #         return obj.x - obj.z
    #     else:
    #         obj.x //= 2
    #         obj.w %= 5
    #         return obj.x + obj.w
    # 字节码 LOAD_ATTR / BINARY_OP / STORE_ATTR
    # / 反编译器在 elif body 内连续属性 augassign 时易错乱操作顺序。
    SOURCE_CODE = """def f(flag, obj):
    if flag == 'a':
        obj.x += 1
        obj.y *= 2
        return obj.x + obj.y
    elif flag == 'b':
        obj.x -= 1
        obj.z **= 3
        return obj.x - obj.z
    else:
        obj.x //= 2
        obj.w %= 5
        return obj.x + obj.w"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
