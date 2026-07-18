import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AnnAssignComplex(ExhaustiveTestCase):
    # if 体内复杂类型注解 ann assign x: List[Dict[str, int]] = {}
    SOURCE_CODE = """if c:
    x: List[Dict[str, int]] = {}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
