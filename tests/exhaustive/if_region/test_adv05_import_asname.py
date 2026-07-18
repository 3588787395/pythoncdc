import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05ImportAsname(ExhaustiveTestCase):
    # if 体内 from-import asname
    SOURCE_CODE = """if c:
    from m import x as y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
