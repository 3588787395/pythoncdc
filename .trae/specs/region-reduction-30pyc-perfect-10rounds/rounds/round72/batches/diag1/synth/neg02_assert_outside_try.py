# F-ASSERT (base.OverNightOrder.__init__): chained-compare asserts are compiled to
# LOAD_ASSERTION_ERROR + jumps; decompiler lowers them to `if not cond: pass` plus a
# separate `raise AssertionError`, which makes every statement after the assert
# unreachable and CPython's peephole pass deletes it (188 -> 165 instructions).
class OverNightOrder:
    def __init__(self, hour, minute, volume):
        assert 0 <= hour < 24
        assert 0 <= minute < 60
        self.order_hour = hour
        self.order_minute = minute
        self.volume = volume
        return None
