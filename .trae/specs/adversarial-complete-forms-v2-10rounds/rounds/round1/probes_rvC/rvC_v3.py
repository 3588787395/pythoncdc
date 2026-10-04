# rvC 变体3：try/finally 外层套 with 与 if（宿主结构混合）。
# 预期：不得比修复前（616437c3，批次 B 在位、批次 C 未在位）更差；
# with 体内 try/finally + for 循环出口块 + finally 语句 res.touch() 保持。
class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def touch(self):
        return 1


def guarded(res, items):
    kept = []
    with _Ctx():
        try:
            for x in items:
                if x > 0:
                    kept.append(x)
        finally:
            res.touch()
    if kept:
        kept.append(None)
    return kept
