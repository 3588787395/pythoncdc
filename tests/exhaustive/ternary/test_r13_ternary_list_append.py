import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryListAppend(ExhaustiveTestCase):
    """Bug R13 (new): lst.append((a if c else b)) — list.append arg ternary。

    原始:
        lst.append((a if c else b))
    缺陷: ternary 作为 list.append 方法的位置参数。cond_block preload 含
         LOAD_NAME lst + LOAD_ATTR append，ternary merge 块作为 append 的
         arg。与 R12 dict_get_default 模式相似但 receiver 是 list 而非 dict。
         验证 method call 模式 ternary 在 arg 位置的统一归约。
    """
    SOURCE_CODE = """lst.append((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
