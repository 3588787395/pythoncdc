# F-OTHER (quote.load_get_price): outer `if` whose body is a single nested
# if/elif chain.  The decompiler hoists the inner chain to the outer level and
# leaves the outer condition behind as a bare expression statement
# (`len(panel.major_axis) != 0`), so the first divergent instruction is
# POP_JUMP_FORWARD_IF_FALSE -> POP_TOP with identical instruction count.
def load_get_price(panel, is_utc, typet):
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet in (1, 2, 3, 4, 5, 13):
                panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    panel.major_axis = panel.major_axis.tz_localize(None)
    return panel
