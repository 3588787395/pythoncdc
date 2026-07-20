import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10DictcompWalrusKey(ExhaustiveTestCase):
    # if 体内 dict comp 中 walrus 在 key {(x := k): v for k, v in d.items()}
    SOURCE_CODE = """if c:
    r = {(x := k): v for k, v in d.items()}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
