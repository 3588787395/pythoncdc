import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10FstringConvFormat(ExhaustiveTestCase):
    # if 体内 f-string 包含 conversion + format spec f"{x!r:>10}"
    SOURCE_CODE = """if c:
    x = f"{y!r:>10}" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
