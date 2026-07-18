import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11FstringDebug(ExhaustiveTestCase):
    # if 体内 f-string 调试语法 f"{x=}"
    SOURCE_CODE = '''if c:
    x = f"{y=}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
