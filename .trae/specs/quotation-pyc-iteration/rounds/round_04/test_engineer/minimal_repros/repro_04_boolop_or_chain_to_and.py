# R4 minimal repro: BOOLOP assert not(or-chain) 误转为 if not(and-chain): assert last_cond
# 关联缺陷：新发现 (R4 新增, check_frequency: or 链 -> and 链 + assert 末位条件)
# 触发区域：BOOLOP + ASSERT
# 预期：assert not (a or b or c or d or e or f), "msg"
# R4 实际产物：if not (a and b and c and d and e and f): assert f, "msg"  (or->and 语义反转)
def check_frequency(frequency):
    global frequency_compat
    if frequency in frequency_compat:
        frequency = frequency_compat.get(frequency)
    assert not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == 'mo' or frequency == '1q' or frequency == '1y'), "您输入的频率有误"
    if frequency not in ('1w', 'mo', '1y', '1q'):
        try:
            tmp = int(frequency[:-1])
        except BaseException:
            raise RuntimeError("X需要是一个正整数")
        else:
            if tmp > 0:
                pass
            else:
                raise RuntimeError("X需要是一个正整数")
    return frequency
