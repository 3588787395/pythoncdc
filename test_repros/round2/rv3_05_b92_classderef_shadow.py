# rv3_05: B92 变体——类体 LOAD_CLASSDEREF 读取 + 同名局部遮蔽组合
# 外层函数闭包变量 x：类体读取（LOAD_CLASSDEREF）；类内方法以 x 作参数名（同名遮蔽）
def make_top(x):
    class Top:
        TV = x
        other = x

        def get_x(self, x):
            return x

        def get_tv(self):
            return self.TV
    return Top


class ShadowCombo:
    def bind(self, y):
        z = y
        class Inner:
            IV = z
            def loc(self, z):
                return z + 1
        return Inner
