import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11FstringDebugFormat(ExhaustiveTestCase):
    # if 体内 f-string 调试语法 + 格式说明符 f"{x=:.2f}"
    SOURCE_CODE = '''if c:
    x = f"{y=:.2f}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
