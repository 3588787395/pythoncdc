import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryDictSetdefault(ExhaustiveTestCase):
    """Bug R13 (new): d.setdefault(k, (a if c else b)) — dict.setdefault 双参数 ternary。

    原始:
        d.setdefault(k, (a if c else b))
    缺陷: ternary 作为 dict.setdefault 的第二个位置参数（default）。cond_block
         preload 含 LOAD_NAME d + LOAD_ATTR setdefault + LOAD_NAME k（第一位置参数），
         ternary merge 块栈输出作为 setdefault 调用第二个位置参数。与 R12
         dict_get_default 单参数变体不同，setdefault 需要 preload 位置参数 k
         与 ternary 共存。验证 method call 双位置参数 + ternary arg 的归约。
    """
    SOURCE_CODE = """d.setdefault(k, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
