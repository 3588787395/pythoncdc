# round-2 r2v3 control (synthetic) — 循环宿主是 for 体（非 if 臂）：既有正确路径，
# 守卫必须不改变其行为
def f(items, TH):
    for x in items:
        while True:
            if TH:
                break
            time.sleep(0.01)
    g()
