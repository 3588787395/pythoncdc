"""repro_06: one_prod_to_dataframe 跳转目标归一化 (i==0 提取外层 if, elif 入口偏移)
区域类型: Conditional
违反原则: 4 (入口引用语义)
对应函数: one_prod_to_dataframe
缺陷镜像: `if i == 0: ... elif i == 1: ... elif i == 2: ... else: ...` 链首个分支被提取为外层 if，
  原始 POP_JUMP_FORWARD_IF_FALSE 跳到下一 elif 入口(idx 175)，反编译产物跳到 idx 394，
  跳转目标指向 elif 链下一分支入口的引用语义未对齐。
  diff_detail idx 131: orig POP_JUMP_FORWARD_IF_FALSE ->[175] vs new ->[394]。
"""


def f(i, x):
    if i == 0:
        x = init(x)
    elif i == 1:
        x = step1(x)
    elif i == 2:
        x = step2(x)
    else:
        x = step3(x)
    return x


def init(a):
    return a


def step1(a):
    return a


def step2(a):
    return a


def step3(a):
    return a
