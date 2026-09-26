# F-ORELSE (wizard_quant_api filter_desicion): `if A or B: return None else: S`
# -- decompiler splits the or-chain into nested ifs and duplicates the body.
def decide(short_values=None, long_values=None):
    if short_values is None or long_values is None:
        return None
    else:
        return down(short_values, long_values)
