# Source Generated with Decompyle++ (Python version)
# File: real_get_real_from_zeromq.pyc (Python 3.11)

def get_real_from_zeromq(self, stocks, typet):
    returnPa = None
    params = ['real']
    if isinstance(stocks, str):
        params.append(stocks)
    elif isinstance(stocks, list):
        for item in stocks:
            params.append(item)
    self.log.quote.debug(f'在线获取real数据，参数为{params[:10]!s}等{len(params) - 1!s}只代码')
    redata, flag = self.api_get_from_multi_zeromq(str(params))
    count = 0
    while not redata and count < 3:
        time.sleep(3)
        if flag == 1:
            self.log.quote.info('获取real数据异常，现在进行第' + str(count + 1) + '次重试')
        elif flag == -1:
            self.log.quote.info('获取real数据返回为空，现在进行第' + str(count + 1) + '次重试')
        redata, flag = self.api_get_from_multi_zeromq(str(params))
        count += 1
    if redata:
        redata = redata.get('data').get('snapshot')
        try:
            if redata:
                data = {}
                columns = ['time', 'open', 'close', 'high', 'low', 'volume', 'money', 'is_open']
                if isinstance(stocks, str):
                    if str(typet) == '6':
                        temp = time.strftime('%Y%m%d', time.localtime(time.time()))
                    else:
                        temp = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
                    returndata = {'time': [temp], 'open': [0], 'close': [0], 'high': [0], 'low': [0], 'volume': [0], 'money': [0], 'is_open': [0]}
                    if stocks in redata:
                        for i, v in enumerate(redata[stocks][:len(columns)]):
                            if i == 0:
                                if str(typet) == '6':
                                    temp = time.strftime('%Y%m%d', time.localtime(time.time()))
                                    returndata[columns[i]] = [temp]
                                    continue
                                temp = time.strftime('%Y%m%d', time.localtime(time.time())) + str(v)[:4].rjust(4, '0')
                                returndata[columns[i]] = [temp]
                                continue
                                continue
                            returndata[columns[i]] = [v]
                            continue
                        if returndata['volume'][0] == 0:
                            returndata['is_open'] = 0
                        else:
                            returndata['is_open'] = 1
                        returnDf = pandas.DataFrame(returndata, columns=columns)
                        returnDf.insert(5, 'price', returnDf['close'])
                        data[stocks] = returnDf
                    else:
                        returnDf = pandas.DataFrame(returndata, columns=columns)
                        returnDf.insert(5, 'price', returnDf['close'])
                        data[stocks] = returnDf
                        self.log.quote.warning(str(stocks) + ' real行情返回异常，内容为空')
                elif isinstance(stocks, list):
                    for item in stocks:
                        if str(typet) == '6':
                            temp = time.strftime('%Y%m%d', time.localtime(time.time()))
                        else:
                            temp = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
                        returndata = {'time': [temp], 'open': [0], 'close': [0], 'high': [0], 'low': [0], 'volume': [0], 'money': [0], 'is_open': [0]}
                        if item in redata:
                            for i, v in enumerate(redata[item][:len(columns)]):
                                if i == 0:
                                    if str(typet) == '6':
                                        temp = time.strftime('%Y%m%d', time.localtime(time.time()))
                                        returndata[columns[i]] = [temp]
                                        continue
                                    temp = time.strftime('%Y%m%d', time.localtime(time.time())) + str(v)[:4].rjust(4, '0')
                                    returndata[columns[i]] = [temp]
                                    continue
                                    continue
                                returndata[columns[i]] = [v]
                                continue
                            if returndata['volume'][0] == 0:
                                returndata['is_open'] = 0
                            else:
                                returndata['is_open'] = 1
                            returnDf = pandas.DataFrame(returndata, columns=columns)
                            returnDf.insert(5, 'price', returnDf['close'])
                            data[item] = returnDf
                            continue
                        returnDf = pandas.DataFrame(returndata, columns=columns)
                        returnDf.insert(5, 'price', returnDf['close'])
                        data[item] = returnDf
                        self.log.quote.warning(str(item) + ' real行情返回异常，内容为空')
                        continue
                returnPa = pandas.Panel(data)
                return (returnPa, 0)
            self.log.quote.warning('real返回数据异常，内容为空')
            return (None, -1)
        except BaseException as x:
            self.log.quote.error('异常走到这里log' + str(x))
            print('异常走到这print')
            import sys
            import os
            exc_type = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('异常信息:', exc_type, fname, exc_tb.tb_lineno)
            self.log.quote.error('real数据处理异常, 更改竟然不能生效' + str(x))
            return (None, 2)
    elif flag == 1:
        self.log.quote.info('real数据转化异常，默认返回空值')
    elif flag == -1:
        self.log.quote.info('real数据返回空值')
    return (None, flag)
