# Source Generated with Decompyle++ (Python version)
# File: r139_01_call_in_or.pyc (Python 3.11)

class C:
    @staticmethod
    def phase():
        return 1
def f(cfg, freq, c):
    dt = 0
    if cfg == '1m':
        if freq == '1d' or C.phase() == 1:
            dt = 2
    return dt
