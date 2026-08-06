"""R35 最小复现实例 4: 仅跳转目标差异"""
# 原始与反编译: 指令序列一致，仅跳转目标地址不同
# 预期: jump_only 应计为匹配

def test_jump_only(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
