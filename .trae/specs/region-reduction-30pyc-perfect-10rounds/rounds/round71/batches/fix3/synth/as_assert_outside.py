# F-ASSERT / negative control: the same chained-compare asserts OUTSIDE any try.
# Reading must stay identical to landed (2 AssertRegions, reach=True).
def window_plain(hour, minute, log):
    h = int(hour)
    m = int(minute)
    assert 0 <= h < 24
    assert 0 <= m < 60
    return h * 60 + m
