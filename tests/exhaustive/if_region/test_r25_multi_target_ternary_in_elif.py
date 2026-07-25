import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25MultiTargetTernaryInElif(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, flag):
    if flag == 'a':
        return 'a'
    elif flag == 'b':
        a = b = (x if x > 0 else 0)
        return a + b
    else:
        return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
