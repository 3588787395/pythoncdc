# Source Generated with Decompyle++ (Python version)
# File: neg02_assert_outside_try.pyc (Python 3.11)

class OverNightOrder:
    def __init__(self, hour, minute, volume):
        assert 0 <= hour < 24
        assert 0 <= minute < 60
        self.order_hour = hour
        self.order_minute = minute
        self.volume = volume
