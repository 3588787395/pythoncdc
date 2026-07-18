import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryPlainTernaryAnd(ExhaustiveTestCase):
    # if 条件中三元 + 普通变量 + 三元 作 and 操作数：
    # if (a if c else b) and d and (e if f else g):
    #     pass
    # 字节码含两段独立三元 merge_block，由外层 and 短路连接，中间夹一个普通变量 d。
    # 两个 TernaryRegion 不连续，中间被 d 隔开，反编译器可能错误归并。
    SOURCE_CODE = """if (a if c else b) and d and (e if f else g):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
