"""repro_03: 集合字面量 `{'a', 'b', ...}` 的常量存储为 tuple vs frozenset（build_future_fill_time）。

build_future_fill_time 的 5 处 LOAD_CONST tuple → frozenset 差异属于 Python 编译器版本差异，
不可通过算法修复。本 repro 用于文档化该差异：原始 pyc 用旧版 Python 编译，set literal 常量存为 tuple；
Python 3.11.15 编译时，set literal 常量存为 frozenset。

镜像 build_future_fill_time 的实际 CFG：
  - for item in total_dts: 循环
  - if typet == 2 and suffix == 'T.CCFX': market_time = {...}
  - elif suffix in ('XZCE', 'XDCE', 'XSGE'): market_time = {...}
  - 集合字面量赋值给 market_time
"""


def build_future_fill_time_repro(typet, suffix, total_dts):
    result = []
    for item in total_dts:
        if typet == 2:
            if suffix == 'T.CCFX':
                market_time = {'14:30:00', '15:15:00', '10:00:00', '13:30:00', '15:00:00'}
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = {'10:00:00', '09:30:00', '11:15:00', '13:45:00'}
            else:
                market_time = {'13:30:00', '10:00:00', '10:30:00', '14:30:00'}
            if item in market_time:
                result.append(item)
        elif typet == 6:
            if suffix == 'T.CCFX':
                market_time = {'11:30:00', '15:00:00', '15:15:00'}
            else:
                market_time = {'11:30:00', '15:00:00', '15:15:00'}
            if item in market_time:
                result.append(item)
    return result
