# Source Generated with Decompyle++ (Python version)
# File: r9q_10_elif_mid_arm_continue.pyc (Python 3.11)

def elif_mid_continue(items, lg):
    for it in items:
        if it == 1:
            lg.info('one')
            continue
        elif it == 2:
            lg.info('two')
        elif it == 3:
            continue
        lg.warn('tail')
