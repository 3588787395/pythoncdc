import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06EllipsisIs(ExhaustiveTestCase):
    # if 体内 Ellipsis 操作 (x is ...)
    SOURCE_CODE = """if c:
    z = x is ..."""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
