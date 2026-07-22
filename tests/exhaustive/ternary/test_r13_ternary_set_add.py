import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernarySetAdd(ExhaustiveTestCase):
    """Bug R13 (new): s.add((a if c else b)) — set.add arg ternary。

    原始:
        s.add((a if c else b))
    缺陷: ternary 作为 set.add 方法的位置参数。cond_block preload 含
         LOAD_NAME s + LOAD_ATTR add，ternary merge 块作为 add 调用的
         arg。验证 set 容器 method call + ternary arg 归约路径。
    """
    SOURCE_CODE = """s.add((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
