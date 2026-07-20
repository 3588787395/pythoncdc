import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10UnionTypeAnn(ExhaustiveTestCase):
    # if 体内 PEP 604 union 类型注解 x: int | None = None
    SOURCE_CODE = """if c:
    x: int | None = None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
