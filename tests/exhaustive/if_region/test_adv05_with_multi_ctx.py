import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05WithMultiCtx(ExhaustiveTestCase):
    # if 体内 with 多上下文管理器
    SOURCE_CODE = """if c:
    with a as x, b as y:
        z = x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
