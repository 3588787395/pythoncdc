import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11DeeplyNestedIfElse(ExhaustiveTestCase):
    # if 体内 5 层嵌套 if/else
    SOURCE_CODE = """if c:
    if a:
        if b:
            if d:
                if e:
                    pass
                else:
                    x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
