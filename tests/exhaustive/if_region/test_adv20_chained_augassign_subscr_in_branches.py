import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20ChainedAugassignSubscrInBranches(ExhaustiveTestCase):
    # if-elif-else body 内含连续 subscr augassign + 多重索引：
    # def f(flag, data):
    #     if flag == 'a':
    #         data['x'] += 1
    #         data['y']['z'] *= 2
    #         return data['x'] + data['y']['z']
    #     elif flag == 'b':
    #         data[0] -= 1
    #         data[1][2] //= 3
    #         return data[0] * data[1][2]
    #     else:
    #         data['k1']['k2']['k3'] **= 2
    #         data['k4'] %= 7
    #         return data['k1']['k2']['k3'] + data['k4']
    # 字节码 LOAD_SUBSCR / BINARY_OP / STORE_SUBSCR
    # / 反编译器在 if-elif-else 三分支都含多重 subscr augassign 时易丢失中间层索引。
    SOURCE_CODE = """def f(flag, data):
    if flag == 'a':
        data['x'] += 1
        data['y']['z'] *= 2
        return data['x'] + data['y']['z']
    elif flag == 'b':
        data[0] -= 1
        data[1][2] //= 3
        return data[0] * data[1][2]
    else:
        data['k1']['k2']['k3'] **= 2
        data['k4'] %= 7
        return data['k1']['k2']['k3'] + data['k4']"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
