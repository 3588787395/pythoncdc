import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryDictcompComplex(ExhaustiveTestCase):
    """Bug R6: ternary 在 dictcomp value + multi-iter 中 — 字节码不一致。

    原始: z = {k: a if c else b for k, v in items}
    缺陷: dictcomp value 是 ternary，且 iter 是 tuple unpack (k, v)。
         期望 dictcomp code object 内部 ternary 正确归约；当前疑似
         dictcomp 的 BUILD_MAP key/value 顺序与 ternary merge 块冲突。
    """
    SOURCE_CODE = """z = {k: a if c else b for k, v in items}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
