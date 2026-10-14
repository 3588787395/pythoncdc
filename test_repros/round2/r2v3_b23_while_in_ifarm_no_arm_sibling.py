# round-2 r2v3 specimen (synthetic) — B107: if 臂唯一语句即循环、且 if 之后无兄弟
# 语句（loop-at-arm-end without a sibling），臂内体尾兄弟必须在环内、不得外提
def f(is_end, TH):
    g()
    if is_end:
        while True:
            if TH:
                break
            time.sleep(0.01)
