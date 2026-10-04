# rvC 变体1：try 体含 for 循环、finally 含语句。
# 预期：FOR_ITER 循环头经正常出口边指向出口块，出口块若被并入
# finally_blocks 应被 [B71] 守卫按正常出口边认领移交 else_blocks；
# finally 语句 sink.append(total) 必须保留（不得蒸发为 finally: pass）。
def sum_items(items, sink):
    total = 0
    try:
        for it in items:
            total += it
    finally:
        sink.append(total)
    return total
