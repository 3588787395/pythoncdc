import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10RaiseFromTernary(ExhaustiveTestCase):
    # if 体内 raise from 三元 raise E from (a if c else b)
    SOURCE_CODE = """if c:
    raise E from (a if cond else b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
