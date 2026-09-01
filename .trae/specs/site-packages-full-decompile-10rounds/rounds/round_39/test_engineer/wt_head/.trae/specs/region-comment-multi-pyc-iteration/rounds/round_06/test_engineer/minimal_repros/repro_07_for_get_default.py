# Pattern: for loop with dict.get(key, None) default (get_security_info inner)
# Function: BasicDataSource.get_security_info
# Expected: for symbol in symbols: asset = d.get(symbol, None)
# Actual: same (pyc 100% match, NO-DEFECT control)
def lookup(symbols, asset_dict):
    result = {}
    for symbol in symbols:
        asset = asset_dict.get(symbol, None)
        if asset:
            result[symbol] = asset
    return result
# NO-DEFECT
