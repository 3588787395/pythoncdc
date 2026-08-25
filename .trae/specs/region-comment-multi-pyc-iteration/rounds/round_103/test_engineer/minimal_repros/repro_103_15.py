def copy_vs_store_multi_assign(d, k, func):
    start_ = d[k] = func()
    return start_
