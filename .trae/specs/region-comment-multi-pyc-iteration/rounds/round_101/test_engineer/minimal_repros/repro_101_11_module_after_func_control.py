# R101-Pattern-D-control: module-level statements after a function whose
# body ends in return; current output sometimes appends spurious
# `while False: pass` blocks between top-level definitions (seen 7x in
# quotationOK.py after api_get_financial / get_market_detail_online).


def first(a):
    return a + 1


def second(b):
    return b * 2


RESULT = (first(1), second(2))
