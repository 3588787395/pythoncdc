# round-2 r2v3 specimen (synthetic) — B107: if 臂是函数体末条，臂内循环以 return 收尾，
# 循环出口汇合块不存在（不得凭空造 else/return None，也不得吞掉环后兄弟）
def f(is_end, TH):
    g()
    if is_end:
        while True:
            if TH:
                return 1
            time.sleep(0.01)
