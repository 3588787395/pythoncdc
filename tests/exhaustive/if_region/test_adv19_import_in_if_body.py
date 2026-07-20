import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19ImportInIfBody(ExhaustiveTestCase):
    # if body 内含 import 语句 + 使用导入的名字：
    # def f(flag):
    #     if flag:
    #         import json
    #         from collections import defaultdict
    #         d = defaultdict(list)
    #         return json.dumps({'a': 1})
    #     return None
    # 字节码 IMPORT_NAME / IMPORT_FROM / STORE_NAME
    # / 反编译器在 if body 内 import + 使用时易丢失 import 或 import_from。
    SOURCE_CODE = """def f(flag):
    if flag:
        import json
        from collections import defaultdict
        d = defaultdict(list)
        return json.dumps({'a': 1})
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
