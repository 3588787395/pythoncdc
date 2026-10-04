"""r10_06: import 深层交叉组合（lambda 默认值/match case/elif 链 × import，深度 ≥3）"""
from m9 import base_value


def imp_combo_lambda_default(rows):
    # import 名作 lambda 默认值 + match 宿主（深度 3：def>for>match>case>if）
    for row in rows:
        match row:
            case {"k": v}:
                from m9 import wrap
                if v > 0:
                    return wrap(v)
            case _:
                pass
    return base_value


def imp_elif_chain_imports(n):
    # if-elif 链各臂 import + alias，链尾 else
    if n < 0:
        from neg.mod import downer as dn
        return dn(n)
    elif n == 0:
        from zero.mod import keeper
        return keeper()
    elif n < 10:
        from small.mod import grower
        return grower(n)
    else:
        from big.mod import shrinker as sk
        return sk(n)
