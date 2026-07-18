import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04LambdaDefaults(ExhaustiveTestCase):
    # lambda 默认值（lambda x=1, y=2: ...）
    SOURCE_CODE = """if (lambda x=1, y=2: x + y)():
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
