import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06AssertFstringMsg(ExhaustiveTestCase):
    # if 体内 assert 带 f-string 复杂 message
    SOURCE_CODE = '''if c:
    assert x > 0, f"msg {y}: {z!r}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
