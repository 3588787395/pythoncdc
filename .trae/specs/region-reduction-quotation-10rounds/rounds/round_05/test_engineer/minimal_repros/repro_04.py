"""repro_04: 复现 <module> 反编译缺陷（模块级函数定义发射到 NOP 占位位置）。

缺陷模式：模块级多个函数定义中，反编译器将部分函数发射到原始字节码的 NOP 占位位置，
导致函数定义顺序错乱、尾部函数丢失（orig=1082, new=1023, diff=-59）。

根因：<module> 字节码含连续 NOP 占位区段（字节码对齐），区域归约时 NOP 块未被正确
归约为占位，函数定义发射位置错乱。
"""


def alpha():
    return 1


def beta():
    return 2


def gamma():
    return 3


def delta():
    return 4


def epsilon():
    return 5
