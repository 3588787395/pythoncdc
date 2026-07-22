import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20GlobalDelInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 global 声明 + 多次修改 + del global key：
    # counter = 0
    # cache = {}
    # def f(flag, key):
    #     global counter, cache
    #     if flag == 'add':
    #         counter += 1
    #         cache[key] = counter
    #         return counter
    #     elif flag == 'del':
    #         if key in cache:
    #             del cache[key]
    #         return len(cache)
    #     else:
    #         old = counter
    #         counter = 0
    #         return old
    # 字节码 LOAD_GLOBAL / STORE_GLOBAL / DELETE_GLOBAL
    # / 反编译器在 if-elif-else 三分支都使用 global 多变量 + del 时易丢失 global 声明。
    SOURCE_CODE = """counter = 0
cache = {}
def f(flag, key):
    global counter, cache
    if flag == 'add':
        counter += 1
        cache[key] = counter
        return counter
    elif flag == 'del':
        if key in cache:
            del cache[key]
        return len(cache)
    else:
        old = counter
        counter = 0
        return old"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
