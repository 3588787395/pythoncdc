import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25DelAttrChainEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(obj, mode):
    if mode == 'a':
        del obj.a.b
    elif mode == 'b':
        del obj.x.y.z
        del obj.p
    else:
        del obj.q.r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
