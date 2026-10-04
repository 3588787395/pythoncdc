"""r10_11: global 基础（读/写/增量赋值全算子面）"""
COUNTER = 0
RATIO = 1.0
LABEL = "init"


def g_write_read(v):
    global COUNTER
    if v > 0:
        COUNTER = v
    for i in range(3):
        if i == 2:
            COUNTER += i
    return COUNTER


def g_augassign_ops(x):
    global RATIO, LABEL
    if x:
        RATIO *= 2
        LABEL += "x"
    else:
        RATIO /= 2
    return (RATIO, LABEL)
