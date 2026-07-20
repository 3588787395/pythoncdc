import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20AssertChainedCmpInBranches(ExhaustiveTestCase):
    # if-elif-else 三分支各自含 assert + 链式比较 + 消息：
    # def f(flag, x):
    #     if flag == 'a':
    #         assert 0 < x < 10, f'out of range: {x}'
    #         return x * 2
    #     elif flag == 'b':
    #         assert 10 < x < 100, 'too small'
    #         return x // 2
    #     else:
    #         assert -100 < x < 0, 'must be neg'
    #         return -x
    # 字节码 LOAD_ASSERTION_ERROR / RAISE_VARARGS / FORMAT_VALUE
    # / 反编译器在 if-elif-else 三分支都含 assert + 链式比较时易丢失消息或结构。
    SOURCE_CODE = """def f(flag, x):
    if flag == 'a':
        assert 0 < x < 10, f'out of range: {x}'
        return x * 2
    elif flag == 'b':
        assert 10 < x < 100, 'too small'
        return x // 2
    else:
        assert -100 < x < 0, 'must be neg'
        return -x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
