# Source Generated with Decompyle++ (Python version)
# File: real_load_bars_from_hundsun.pyc (Python 3.11)

def load_bars_from_hundsun(self, stocks, typet, start, end):
    self.log.quote.debug(f'调用函数load_bars_from_hundsun，参数为：stocks={stocks[:10]!s}等{len(stocks) if isinstance(stocks, list) else 1!s}只代码,typet={typet!s},start={start!s},end={end!s}')
    data = collections.OrderedDict()
    retpanel = pandas.Panel()
    if os.path.exists(DumploadDailyFile) and typet == 6:
        if isinstance(stocks, str):
            stocks = [stocks]
        from fly.dumpload import load_daily
        if self.dumpload_date != self.get_today():
            reload(load_daily)
            self.dumpload_date = self.get_today()
        dailypanel = load_daily.cshare
        if not dailypanel.empty:
            source_start = qdt.datetime.strptime(start[:8] + (len(start[8:]) == 4 and start[8:] or '0000'), '%Y%m%d%H%M')
            source_end = qdt.datetime.strptime(end[:8] + (len(end[8:]) == 4 and end[8:] or '1530'), '%Y%m%d%H%M')
            diffset = set(stocks).difference(set(dailypanel.items))
            if len(diffset) == 0:
                dailypanel = dailypanel.ix[:, source_start:source_end]
                retpanel = dailypanel.ix[stocks, :]
                self.log.quote.debug('调用DumploadDailyFile缓存')
                return retpanel
            if len(diffset) < len(stocks):
                sectionstocks = list(set(stocks).intersection(set(dailypanel.items)))
                dailypanel = dailypanel.ix[:, source_start:source_end]
                retpanel = dailypanel.ix[sectionstocks, :]
                stocks = list(diffset)
                self.log.quote.debug('部分调用DumploadDailyFile缓存')
    if retpanel.empty:
        self.log.quote.debug('未调用DumploadDailyFile缓存')
    if isinstance(stocks, str):
        start_temp = start
        end_temp = end
        klines = self.load_minute_or_day_kline(stocks, typet, start_temp, end_temp)
        if klines is not None and 'price' not in klines:
            klines.insert(5, 'price', klines['close'])
        data[stocks] = klines
    elif isinstance(stocks, list):
        for stock in stocks:
            start_temp = start
            end_temp = end
            klines = self.load_minute_or_day_kline(stock, typet, start_temp, end_temp)
            if klines is not None and 'price' not in klines:
                klines.insert(5, 'price', klines['close'])
            data[stock] = klines
    panel = pandas.Panel(data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money', 'is_open'])
    if len(data) > 0:
        source_start = qdt.datetime.strptime(start[:8] + (len(start[8:]) == 4 and start[8:] or '0000'), '%Y%m%d%H%M')
        source_end = qdt.datetime.strptime(end[:8] + (len(end[8:]) == 4 and end[8:] or '1530'), '%Y%m%d%H%M')
        panel = panel.ix[:, source_start:source_end]
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet in (1, 2, 3, 4, 5, 13):
                panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
            else:
                panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
        elif typet == 6:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    if not retpanel.empty:
        panel = pandas.concat([retpanel, panel], axis=0)
    return panel
