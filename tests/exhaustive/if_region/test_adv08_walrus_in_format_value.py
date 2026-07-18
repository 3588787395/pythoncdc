import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08WalrusInFormatValue(ExhaustiveTestCase):
    # if 体内 f-string 含 walrus: f"{(n := x)}"
    SOURCE_CODE = '''if c:
    s = f"{(n := x)}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
