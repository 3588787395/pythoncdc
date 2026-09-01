
def test():
    max_turnover_ratio_count_list = []
    for factor_info in []:
        factor = factor_info['factor']
        if factor == 'last_turnover_ratio':
            max_turnover_ratio_count_list.append(1)
            continue
        elif factor in ('a', 'b'):
            max_turnover_ratio_count_list.append(1)
            continue
