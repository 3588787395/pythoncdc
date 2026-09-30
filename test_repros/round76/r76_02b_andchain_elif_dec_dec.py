# Source Generated with Decompyle++ (Python version)
# File: r76_02b_andchain_elif_dec.pyc (Python 3.11)

def f(panel, is_utc, typet):
    if len(panel) != 0 and is_utc == '0':
        panel.convert('Asia/Shanghai')
    elif typet in (1, 2, 3):
        panel.localize('UTC')
    return panel
