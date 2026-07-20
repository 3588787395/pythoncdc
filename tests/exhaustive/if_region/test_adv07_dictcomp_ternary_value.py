import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07DictcompTernaryValue(ExhaustiveTestCase):
    # if 体内 dictcomp 带三元作 value: {k: (v if cond else w) for k, v in items}
    SOURCE_CODE = """if c:
    r = {k: (v if cond else w) for k, v in items}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
