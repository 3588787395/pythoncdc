# Source Generated with Decompyle++ (Python version)
# File: b05_bareexcept_boolop_orchain.pyc (Python 3.11)

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
        if ')' in stock_tmp and ']' not in stock_tmp:
            count = position_params_info.split(',')[-1]
            stock = position_params_info.replace(count, '')
            stock = stock[:-1]
        else:
            stock = stock_tmp
            count = count_tmp
    return (stock, count)
