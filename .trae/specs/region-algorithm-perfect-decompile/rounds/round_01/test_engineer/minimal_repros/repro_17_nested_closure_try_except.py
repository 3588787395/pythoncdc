def func_set_slippage_convert_code(code):
    func = 'set_slippage'
    pattern = '\\bset_slippage\\((.*)\\)'
    new_args = []
    def replace_args(match):
        match_group_0 = match.group(0)
        match_group_1 = match.group(1)
        if 'FixedSlippage' in match_group_1:
            new_args.append('slippage=FixedSlippage')
            return 'set_slippage(FixedSlippage)'
        return match_group_0
    def replace_args_FixedSlippage(match):
        match_group_0 = match.group(0)
        try:
            params = eval(match_group_1)
            rate = params[0]
        except:
            rate = match_group_1.split(',')[0]
        return 'FixedSlippage({})'.format(rate)
    import re
    new_code = re.sub(pattern, replace_args, code)
    return new_code
