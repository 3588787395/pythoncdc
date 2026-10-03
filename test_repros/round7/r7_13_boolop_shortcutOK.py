# Source Generated with Decompyle++ (Python version)
# File: r7_13_boolop_shortcut.pyc (Python 3.11)

__doc__ = 'R7-13 BoolOp 短路副作用面（调用序列保持）。'
def s_and_call_seq(log, a, b):
    return log.a() and log.b()
def s_and_or_call_seq(log, a):
    return log.a() and log.b() or log.c()
def s_or_call_seq(log, a):
    return log.fail() or log.recover() or a
def s_not_call(log):
    return not log.check()
def s_shortcut_in_if(log, x):
    if x > 0 and log.ready():
        return log.run()
    return None
def s_call_chain_assign(log, a, b):
    r = log.a() and b or a
    return r
