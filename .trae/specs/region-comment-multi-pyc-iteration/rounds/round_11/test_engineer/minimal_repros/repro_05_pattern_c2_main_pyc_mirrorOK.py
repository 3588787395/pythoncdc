# Source Generated with Decompyle++ (Python version)
# File: repro_05_pattern_c2_main_pyc_mirror.pyc (Python 3.11)

__doc__ = """[R11 repro_05] Pattern C2: exact mirror of main.pyc _adjust_start_date.

Real-world pattern: tuple unpack of two attribute-chain loads inside an
else branch of a function.  This is the exact structure from
IQEngine/main.pyc that exposes Pattern C2.
"""
def _adjust(config, data_proxy):
    if config.run_type == 1:
        return None
    else:
        origin_start_date, origin_end_date = (config.start_date, config.end_date)
        if len(data_proxy.get(origin_start_date, origin_end_date)) == 0:
            raise ValueError('empty')
        return origin_start_date
