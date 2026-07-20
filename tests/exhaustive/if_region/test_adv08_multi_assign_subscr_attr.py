import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08MultiAssignSubscrAttr(ExhaustiveTestCase):
    # if 体内多目标赋值链 a = b[k] = c.d = e
    SOURCE_CODE = """if c:
    a = b[k] = c.d = e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
