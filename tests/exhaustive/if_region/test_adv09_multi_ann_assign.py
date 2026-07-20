import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09MultiAnnAssign(ExhaustiveTestCase):
    # if 体内多个类型注解（混合带值/无值）
    SOURCE_CODE = """if c:
    x: int
    y: str = "hello"
    z: List[int] = []"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
