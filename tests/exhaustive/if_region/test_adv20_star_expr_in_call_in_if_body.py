import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20StarExprInCallInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 star expr 在 call 中 + dict 双星 + 混合：
    # def f(flag, items, extra):
    #     if flag == 'a':
    #         return sorted(*items, key=lambda x: -x, **extra)
    #     elif flag == 'b':
    #         return [f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]
    #     else:
    #         return {**extra, 'sum': sum(items), 'count': len(items)}
    # 字节码 DICT_MERGE / CALL_FUNCTION_EX / BUILD_MAP
    # / 反编译器在 if-elif-else 三分支都含 *args/**kwargs 混合时易丢失星号。
    SOURCE_CODE = """def f(flag, items, extra):
    if flag == 'a':
        return sorted(*items, key=lambda x: -x, **extra)
    elif flag == 'b':
        return [f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]
    else:
        return {**extra, 'sum': sum(items), 'count': len(items)}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
