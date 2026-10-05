# rv3_04: B91 变体——类体 match 真 guard 与假 guard 各一
# 真 guard：case 臂带 `if val:` 运行时可真条件；假 guard：`if 0:`（编译器常量折叠形态）
_TH = 1


class MatchTrueGuard:
    val = _TH
    picked = 0

    match val:
        case 1:
            picked = 11
        case _ if val:
            picked = 12


class MatchFakeGuard:
    val = _TH
    picked = 0

    match val:
        case 1 if 0:
            picked = 21
        case _:
            picked = 22


def use_both():
    return MatchTrueGuard.picked, MatchFakeGuard.picked
