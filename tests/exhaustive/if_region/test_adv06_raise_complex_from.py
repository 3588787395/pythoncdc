import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06RaiseComplexFrom(ExhaustiveTestCase):
    # if 体内 raise 链带构造器参数
    SOURCE_CODE = """if c:
    raise E(a, b=k) from exc"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
