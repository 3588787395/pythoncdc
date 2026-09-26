# Source Generated with Decompyle++ (Python version)
# File: b07_outer_if_hoisted_dangling_cond.pyc (Python 3.11)

def load_get_price(panel, is_utc, typet):
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet in (1, 2, 3, 4, 5, 13):
                panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    panel.major_axis = panel.major_axis.tz_localize(None)
    return panel
