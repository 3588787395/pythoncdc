"""repro_07: 复现 load_bars_from_hundsun 反编译缺陷（函数体大幅截断 -174）。

缺陷模式：if-then 分支内嵌套 if-else，then 分支在嵌套 if 的跳转目标处被截断，
导致 if-then 分支体及尾部 pandas.Panel 构造大量丢失（orig=501, new=327, diff=-174）。

根因：if-then 分支内嵌套 if-else 归约时，then 分支目标计算过短，提前收敛于
嵌套 if 的跳转目标，后续 `if len(data) > 0:` 包裹层与 Panel 构造全部丢失。
"""


def load_bars(cond, typet, stocks):
    retpanel = None
    if cond:
        if typet == 6:
            if isinstance(stocks, str):
                stocks = [stocks]
            panel = load(stocks)
            if len(panel) > 0:
                retpanel = panel
        else:
            retpanel = load(typet)
    return retpanel
