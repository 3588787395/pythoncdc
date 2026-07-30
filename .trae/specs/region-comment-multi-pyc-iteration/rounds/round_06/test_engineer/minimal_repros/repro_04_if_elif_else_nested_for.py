# Pattern: if/elif/else with nested for loop (get_security_info_lru)
# Function: BasicDataSource.get_security_info_lru
# Expected: if symbols: ...if asset: ...else: ... else: for...for...
# Actual: same (pyc 100% match, NO-DEFECT control)
def get_security_info_lru(symbols=None):
    result_dict = {}
    if symbols:
        asset = symbols
        if asset:
            tmp_dict = {}
            for key in ['a', 'b']:
                tmp_dict[key] = key
            result_dict[symbols] = tmp_dict
        else:
            result_dict[symbols] = {}
    else:
        for symbol in ['x']:
            tmp_dict = {}
            for key in ['a']:
                tmp_dict[key] = key
            result_dict[symbol] = tmp_dict
    return result_dict
# NO-DEFECT
