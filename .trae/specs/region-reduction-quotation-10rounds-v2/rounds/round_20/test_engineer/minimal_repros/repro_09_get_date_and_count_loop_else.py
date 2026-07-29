"""repro_09: get_date_and_count 根因 B — _find_loop_else 误识别 else_blocks。

模拟 get_date_and_count 的 while 无 break 模式：_find_loop_else 在 while 无 break 时
误识别 else_blocks，导致循环后语句被错误归入循环 else 分支。R13 尝试"无 break 不识别
else_blocks"导致 -27→-63 退化已回退。

后续迭代建议：_find_loop_else 增加无 break 守卫，但需先解决 IfRegion else-branch 块
收集穿透嵌套 LoopRegion（避免误吸收循环后语句）。
"""


def f(data):
    i = 0
    result = []
    while i < len(data):
        if data[i] > 0:
            result.append(data[i])
        i += 1
    return result
