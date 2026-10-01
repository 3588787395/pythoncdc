# rv_06 修复二 while 双向续接 嵌套变体 2：
# `while a and b or c:` 位于类方法内（类 > 函数 > while），带 if-break


class RV06:
    def run(self, a, b, c):
        n = 0
        while a and b or c:
            n += 1
            if n > 5:
                break
        return n
