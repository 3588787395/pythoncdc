# Source Generated with Decompyle++ (Python version)
# File: default_real_quote.pyc (Python 3.11)

from IQData.interface import AbstractRealQuoteData
class DefaultRealQuote(AbstractRealQuoteData):
    __doc__ = """
    实时数据源类, AbstractRealQuoteData
    """
    def subscribe(self, symbols, sub_type):
        """
        快照数据订阅
        :param symbols:
        :param sub_type:
        :return:
        """
    def unsubscribe(self, symbols):
        """

        :param symbols:
        :return:
        """
    def get_snapshot(self, symbol):
        return None
    def get_kline_by_count(self, symbol, query_date, count, frequency, fields, fq, skip_suspended, include):
        """

        :param symbol:
        :param query_date:
        :param count:
        :param frequency:
        :param fields:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
    def get_kline_by_date(self, symbol, start_date, end_date, frequency, fq, skip_suspended, include):
        """

        :param symbol:
        :param start_date:
        :param end_date:
        :param frequency:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
    def get_real_minute_kline(self, symbol, include=True):
        return None
    def get_real_daily_kline(self, symbol):
        return None
    def get_transaction_data(self, symbols, data_count=50, start_pos=0, search_direction=1):
        return None
    def get_order_data(self, symbols, data_count=50, start_pos=0, search_direction=1):
        return None
    def get_kline_by_count(self, symbol, query_date, count, frequency, fields, fq, skip_suspended, include):
        """

        :param symbol:
        :param query_date:
        :param count:
        :param frequency:
        :param fields:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
    def get_kline_by_date(self, symbol, start_date, end_date, frequency, fq, skip_suspended, include):
        """

        :param symbol:
        :param start_date:
        :param end_date:
        :param frequency:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
