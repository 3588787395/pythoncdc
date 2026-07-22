import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20ChainedMethodCallInBranches(ExhaustiveTestCase):
    # if-elif-else 三分支都含链式方法调用 + 链式 subscr + 比较：
    # def f(flag, data):
    #     if flag == 'a':
    #         return data.strip().lower().split(' ')
    #     elif flag == 'b':
    #         return data.get('key', {}).items().__len__()
    #     else:
    #         return data[0]['name'].upper().replace('A', 'B')[::-1]
    # 字节码 LOAD_ATTR / LOAD_METHOD / CALL / BINARY_SUBSCR
    # / 反编译器在 if-elif-else 三分支都含多层链式方法 + subscr 时易丢失中间层调用。
    SOURCE_CODE = """def f(flag, data):
    if flag == 'a':
        return data.strip().lower().split(' ')
    elif flag == 'b':
        return data.get('key', {}).items().__len__()
    else:
        return data[0]['name'].upper().replace('A', 'B')[::-1]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
