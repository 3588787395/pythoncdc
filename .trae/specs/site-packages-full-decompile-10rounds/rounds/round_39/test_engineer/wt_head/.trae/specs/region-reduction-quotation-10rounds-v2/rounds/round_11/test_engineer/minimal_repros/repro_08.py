"""repro_08: change_his_to_backward for 循环内嵌 if 的 else 体 + 跳转目标偏移
区域类型: Loop + Conditional
违反原则: 4 (入口引用语义)
对应函数: change_his_to_backward
缺陷镜像: `for it in items: if it is not None: ... else: ...` 的 else 体已恢复，
  但 POP_JUMP_FORWARD_IF_NOT_NONE 跳转目标偏移，for-if 嵌套区域出口引用语义未对齐。
  diff_detail idx 296: orig POP_JUMP_FORWARD_IF_NOT_NONE ->[330] vs new ->[342]。
"""


def f(items):
    out = []
    for it in items:
        if it is not None:
            out.append(it)
        else:
            out.append(0)
    return out
