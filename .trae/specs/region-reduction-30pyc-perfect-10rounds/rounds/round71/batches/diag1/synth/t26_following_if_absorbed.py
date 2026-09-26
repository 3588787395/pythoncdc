# F-THENOVER (klinedata.get_history_common): a following `if is_dict:` guard is
# absorbed into the previous then-branch, so that branch's exit jump skips it
# (A@254 -> 446 vs B -> 610, delta +164).
def get_history_common(fq, is_dict, fields, frequency, VALID_DAY, VALID):
    tmp_dividends = None
    if fq is not None:
        symbols_new_list = ['600000.SS']
        tmp_dividends = len(symbols_new_list)
    if not is_dict:
        if fields is None:
            if frequency == '1d':
                field_ori = VALID_DAY.copy()
            else:
                field_ori = VALID.copy()
        elif isinstance(fields, str):
            field_ori = [fields]
        else:
            field_ori = fields
    return tmp_dividends, field_ori
