# Source Generated with Decompyle++ (Python version)
# File: r76_02_andchain_leading.pyc (Python 3.11)

def f(panel, is_utc, typet):
    panel = load(panel)
    if len(panel.major_axis) != 0:
        if is_utc == '0' and typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    return panel
