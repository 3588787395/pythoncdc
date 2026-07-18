import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11RelativeImport(ExhaustiveTestCase):
    # if 体内相对导入 from . import a
    SOURCE_CODE = """if c:
    from . import a"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
