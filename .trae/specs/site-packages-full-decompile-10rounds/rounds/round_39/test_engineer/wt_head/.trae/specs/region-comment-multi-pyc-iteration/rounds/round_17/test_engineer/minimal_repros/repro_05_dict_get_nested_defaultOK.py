# Source Generated with Decompyle++ (Python version)
# File: repro_05_dict_get_nested_default.pyc (Python 3.11)

def get_pe(info):
    pe_low = float(info[0].get('pe_times_low', -999999))
    pe_high = float(info[0].get('pe_times_high', info[0].get('pe_times', 0)))
    return pe_low + pe_high
