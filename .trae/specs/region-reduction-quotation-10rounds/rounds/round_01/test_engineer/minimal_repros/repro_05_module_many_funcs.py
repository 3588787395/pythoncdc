"""repro_05: 模块级连续函数定义丢失（<module> 模式）。

复现原始字节码结构：模块级连续定义多个函数（含装饰器 + 普通函数），
反编译器在某个函数后丢失后续所有函数定义（少 59 条指令）。
对应 _identify_sequence_regions / _generate_basic_region 模块级序列归约。
"""


def func_01(x):
    return x + 1


def func_02(x):
    return x + 2


def func_03(x):
    return x + 3


def func_04(x):
    return x + 4


def func_05(x):
    return x + 5


def func_06(x):
    return x + 6


def func_07(x):
    return x + 7


def func_08(x):
    return x + 8


def func_09(x):
    return x + 9


def func_10(x):
    return x + 10


def func_11(x):
    return x + 11


def func_12(x):
    return x + 12
