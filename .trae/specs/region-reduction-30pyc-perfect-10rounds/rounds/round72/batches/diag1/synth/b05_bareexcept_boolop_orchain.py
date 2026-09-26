# F-BOOLOP (jq_trans_module replace_args x2): or-chain with a trailing and-chain
# operand inside a bare except handler loses one operand test.
def rep(position_params_info):
    try:
        params = eval(position_params_info)
        stock = params[0]
        if "'" not in stock:
            stock = repr(stock)
        count = str(params[1])
    except:
        stock_tmp = position_params_info.split(',')[0]
        count_tmp = position_params_info.split(',')[1]
        if '(' not in stock_tmp or ')' in stock_tmp and ']' not in stock_tmp:
            count = position_params_info.split(',')[-1]
            stock = position_params_info.replace(count, '')
            stock = stock[:-1]
        else:
            stock = stock_tmp
            count = count_tmp
    return stock, count
