# Source Generated with Decompyle++ (Python version)
# File: real_get_individual_data.pyc (Python 3.11)

def get_individual_data(self, data_type, stocks, data_count, start_pos, search_direction):
    """
        获取逐笔行情
        """
    if stocks:
        data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
        if isinstance(stocks, str):
            param = [data_type, [stocks], str(search_direction), str(data_count), str(start_pos)]
        elif isinstance(stocks, (list, tuple)):
            param = [data_type, list(stocks), str(search_direction), str(data_count), str(start_pos)]
        redata, flag = self.api_get_from_zeromq(str(param))
        count = 0
        while not redata and count < 3:
            time.sleep(1)
            if flag == 1:
                self.log.quote.info('获取逐笔数据异常，现在进行第' + str(count + 1) + '次重试')
            elif flag == -1:
                self.log.quote.info('获取逐笔数据返回为空，现在进行第' + str(count + 1) + '次重试')
            redata, flag = self.api_get_from_zeromq(str(param))
            count += 1
        if redata:
            redata = redata.get('data').get(data_type)
            try:
                if redata:
                    data = {}
                    columns = redata.get('fields')
                    if isinstance(stocks, str):
                        data_list = redata.get(stocks)
                        if not data_list:
                            self.log.quote.warning('当前代码%s返回逐笔数据为空' % stocks)
                            data_list = []
                        data_df = pandas.DataFrame(data_list, columns=columns)
                        data[stocks] = data_df
                    elif isinstance(stocks, (list, tuple)):
                        for stock in stocks:
                            data_list = redata.get(stock)
                            if not data_list:
                                self.log.quote.warning('当前代码%s返回逐笔数据为空' % stock)
                                data_list = []
                            data_df = pandas.DataFrame(data_list, columns=columns)
                            data[stock] = data_df
                    returnPa = pandas.Panel(data)
                    return returnPa
                self.log.quote.warning('逐笔数据接口返回异常，内容为空')
                return None
            except BaseException as x:
                self.log.quote.error('逐笔成交数据处理异常:' + str(x))
                return None
        elif flag == 1:
            self.log.quote.info('逐笔数据转化异常，默认返回空值')
        elif flag == -1:
            self.log.quote.info('逐笔数据返回空值')
        return None
    else:
        return None
