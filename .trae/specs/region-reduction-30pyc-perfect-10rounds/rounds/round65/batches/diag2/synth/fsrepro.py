
class C:
    def m_a(self, universe):
        self.log.quote.debug(f'初始化imagedata,包括{universe[:10]}等{len(universe)}只代码')
        redata, flag = self.api_get(str(params))
        count = 0
        return redata

    def m_b(self, security, frequency, start_date):
        self.log.quote.debug(f'调用函数get_price，参数为：stocks={security[:10]}等{len(security) if isinstance(security, list) else 1}只代码,frequency={frequency}')
        candle_period = None
        self.check_datetime(start_date)
        return candle_period

    def m_c(self, universe):
        self.log.quote.debug(f'包括{universe[:10]}等{len(universe)}只代码')
        return 1

    def m_d(self, universe):
        self.log.debug(f'包括{universe}码')
        return 1

    def m_e(self, universe):
        self.log.debug(f'包括{universe[:10]}码')
        return 1
