import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06FstringConversion(ExhaustiveTestCase):
    # if 体内 f-string 带 conversion (!r, !s, !a)
    SOURCE_CODE = '''if c:
    s = f"{x!r} {y!s} {z!a}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
