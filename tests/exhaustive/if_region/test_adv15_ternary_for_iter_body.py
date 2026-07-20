import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryForIterBody(ExhaustiveTestCase):
    # if 体内 for 循环的 iterable 为三元表达式：
    # if c:
    #     for x in (a if p else b):
    #         pass
    # 字节码 LOAD_NAME c / 含三元 merge_block（cond=p 选择 a / b）
    # / GET_ITER / FOR_ITER / STORE_NAME x / ... 反编译器在归约
    # 三元 merge 与 GET_ITER/FOR_ITER 时出错，将三元 merge 拆出
    # 为独立表达式语句（POP_TOP），同时 for 循环的 iterable 仍
    # 保留三元表达式但缺少括号，导致三元被求值两次（一次作为
    # 独立语句，一次作为 iterable），指令数不匹配。
    SOURCE_CODE = """if c:
    for x in (a if p else b):
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
