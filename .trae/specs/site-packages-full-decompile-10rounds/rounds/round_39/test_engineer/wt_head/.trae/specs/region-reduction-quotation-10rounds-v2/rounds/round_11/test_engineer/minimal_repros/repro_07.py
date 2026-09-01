"""repro_07: build_future_fill_time listcomp code 对象布局 + 跳转目标偏移
区域类型: Sequence + Conditional
违反原则: 4 (入口引用语义)
对应函数: build_future_fill_time
缺陷镜像: listcomp 内部 code 对象生成后，后续 JUMP_FORWARD 跳转目标偏移，
  listcomp 抽象节点出口引用语义未对齐。
  diff_detail idx 226: orig JUMP_FORWARD ->[649] vs new ->[629]。
"""


def f(times):
    filled = [t for t in times if t > 0]
    if filled:
        result = filled[0]
    else:
        result = None
    return result
