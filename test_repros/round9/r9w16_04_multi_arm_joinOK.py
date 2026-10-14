# Source Generated with Decompyle++ (Python version)
# File: r9w16_04_multi_arm_join.pyc (Python 3.11)

def r9w16_04_multi_arm_join(q, log):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if x.a:
                log('a')
            elif x.b:
                log('b')
            else:
                log('c')
        sleep(0.001)
