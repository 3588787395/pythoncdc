import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06FstringDebugSpec(ExhaustiveTestCase):
    # if 体内 f-string debug spec f"{x=}"
    SOURCE_CODE = '''if c:
    s = f"{x=} {y=}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
