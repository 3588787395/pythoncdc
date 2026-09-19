"""R3-H: and 链（not 操作数）被重写为嵌套 if + 显式 continue。
对照 quote.pyc filter_stock_by_status 循环体:
    if not ST_result.get(stock) and not HALT_result.get(stock) and not DELISTING_result.get(stock) and not DELISTING_SORTING_result.get(stock):
        result.append(stock)
orig 编译为 4 条 POP_JUMP_FORWARD_IF_TRUE 直达循环底; 反编译输出嵌套 if + 3 条独立 JUMP_BACKWARD。"""


def filter_stock_by_status(self, stocks, filter_type=('ST', 'HALT', 'DELISTING')):
    result = []
    date_today = qdt.datetime.now().strftime('%Y%m%d')
    query_date = date_today
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        stocks = stocks
    else:
        system_log.error('暂只支持str或list类型股票数据')
        return result
    try:
        ST_result = {}
        HALT_result = {}
        DELISTING_result = {}
        DELISTING_SORTING_result = {}
        if query_date >= date_today:
            if 'ST' in filter_type:
                ST_result = self.is_ST_stock_real(stocks)
            if 'HALT' in filter_type:
                HALT_result = self.is_halt_stock_real(stocks)
            if 'DELISTING' in filter_type:
                DELISTING_result = self.is_delisting_stock_real(stocks)
            if 'DELISTING_SORTING' in filter_type:
                DELISTING_SORTING_result = is_delisting_sorting_stock_real(stocks)
        for stock in stocks:
            if not ST_result.get(stock) and not HALT_result.get(stock) and not DELISTING_result.get(stock) and not DELISTING_SORTING_result.get(stock):
                result.append(stock)
        return result
    except BaseException:
        system_log.error(get_traceback_message())
        return result
