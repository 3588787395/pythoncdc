# rv_07 修复二 comprehension 甄别窗 嵌套变体 1：
# listcomp 混合过滤器位于类方法内（类 > 函数 > 推导式）
# 验收：深层与浅层 r1_21 产物一致（MATCH，含 MAKE_CELL）


class RV07:
    def pick(self, vals, a, b, c):
        picked = [v for v in vals if a and b or c]
        return len(picked)
