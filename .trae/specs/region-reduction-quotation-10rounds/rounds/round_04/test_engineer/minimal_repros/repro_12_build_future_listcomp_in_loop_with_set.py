"""repro_12: listcomp + set literal 在循环内 + JUMP_FORWARD 跳转目标偏移（build_future 变体）。

build_future_fill_time 的 JUMP_FORWARD 偏移 74 字节源于 frozenset 常量差异的连锁后果。
本 repro 镜像 listcomp + set literal 在循环内的结构，验证 listcomp 归约是否影响 JUMP_FORWARD 跳转目标。

镜像 build_future_fill_time 的实际 CFG：
  - for item in total_dts:（外层循环）
    - if typet == 2 and suffix == 'T.CCFX':
      - market_time = [x for x in items if x in {'09:30', '10:00', '11:30'}]  # listcomp + set
    - elif typet == 6: ...
  - JUMP_FORWARD 到函数末尾（return）
"""


def build_future_variant(typet, suffix, total_dts, items):
    result = []
    for item in total_dts:
        if typet == 2:
            if suffix == 'T.CCFX':
                market_time = {'14:30:00', '15:15:00', '10:00:00', '13:30:00', '15:00:00'}
                filtered = [x for x in items if x in market_time]
                result.extend(filtered)
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = {'10:00:00', '09:30:00', '11:15:00', '13:45:00'}
                if item in market_time:
                    result.append(item)
        elif typet == 6:
            if suffix == 'T.CCFX':
                market_time = {'11:30:00', '15:00:00', '15:15:00'}
                if item in market_time:
                    result.append(item)
    return result
