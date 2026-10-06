# round-2 r2v3 specimen (synthetic) — B107: 循环在 if 臂内且不是臂首条语句，
# 体尾兄弟 + 环后兄弟（认领点 = 臂的非首块）
def f(is_end, TH):
    if is_end:
        bus = get_bus()
        while True:
            if TH:
                break
            time.sleep(0.01)
    publish(bus)
