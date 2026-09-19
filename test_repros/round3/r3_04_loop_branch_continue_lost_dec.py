# Source Generated with Decompyle++ (Python version)
# File: r3_04_loop_branch_continue_lost.pyc (Python 3.11)

__doc__ = """R3-D: for 循环内 if/elif 链首分支的 continue（隐式回边）丢失 → 分支落入链尾语句被覆盖。
对照 quote.pyc is_ST_stock_real / is_delisting_stock_real:
    O35 JUMP_BACKWARD to 92 (continue) 被反编译为 JUMP_FORWARD 到链尾 → result[i]=False 覆盖 True。"""
def is_st_stock_real(self, stocks):
    result = {}
    stock_name_dict = self.get_stock_name_real(stocks)
    if len(stock_name_dict) > 0:
        for i in stocks:
            stock_name = stock_name_dict.get(i, '')
            if 'ST' in stock_name or 'PT' in stock_name:
                result[i] = True
                continue
            elif stock_name == '':
                result[i] = None
                continue
            result[i] = False
    else:
        for i in stocks:
            result[i] = None
    return result
def is_delisting_stock_real(self, stocks):
    all_stocks_list = []
    f = open('/home/fly/data/BasicInfo/market_stocks_all.txt', 'r')
    lines = f.readlines()
    for line in lines:
        all_stocks_list.append(line.strip())
    result = {}
    for i in stocks:
        stock = i.replace('XSHE', 'SZ').replace('XSHG', 'SS')
        if stock not in all_stocks_list:
            continue
        stock_status = self.image_data.get(stock).get('trade_status', '')
        if stock_status == 'DELISTED':
            result[i] = True
            continue
        result[i] = False
    return result
