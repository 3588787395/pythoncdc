import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20NonlocalMultiInElifBranches(ExhaustiveTestCase):
    # if-elif-else 三分支都含 nonlocal 多变量 + 嵌套闭包修改：
    # def f(flag):
    #     total = 0
    #     count = 0
    #     items = []
    #     def update():
    #         nonlocal total, count, items
    #         if flag == 'add':
    #             total += 1
    #             count += 1
    #             return total + count
    #         elif flag == 'reset':
    #             total = 0
    #             count = 0
    #             items.clear()
    #             return 0
    #         else:
    #             items.append(total)
    #             return len(items)
    #     return update()
    # 字节码 LOAD_DEREF / STORE_DEREF / LOAD_CLOSURE
    # / 反编译器在 if-elif-else 三分支都含 nonlocal 多变量时易丢失 nonlocal 声明。
    SOURCE_CODE = """def f(flag):
    total = 0
    count = 0
    items = []
    def update():
        nonlocal total, count, items
        if flag == 'add':
            total += 1
            count += 1
            return total + count
        elif flag == 'reset':
            total = 0
            count = 0
            items.clear()
            return 0
        else:
            items.append(total)
            return len(items)
    return update()"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
