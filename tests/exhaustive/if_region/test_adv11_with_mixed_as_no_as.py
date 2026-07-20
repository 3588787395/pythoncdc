import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11WithMixedAsNoAs(ExhaustiveTestCase):
    # if 体内 with 多 ctx 部分有 as 部分无 as
    SOURCE_CODE = """if c:
    with x as y, z:
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
