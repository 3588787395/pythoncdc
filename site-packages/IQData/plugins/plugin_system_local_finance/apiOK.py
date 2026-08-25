# Source Generated with Decompyle++ (Python version)
# File: api.pyc (Python 3.11)

from IQData.engine import Engine
from IQData.api.api_base import api_method
@api_method
def get_fundamentals(security, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, date_type=None, merge_type=None):
    """
    财务数据接口：包括三大财报、六大成长指标、股本信息、估值数据
    :param security：股票代码，str/list，非空
    :param table：表名
    :param fields：获取字段，str/list，非空
    :param date：日期
    :param start_year：开始年份
    :param end_year：截止年份
    :param report_types：季度
    :param date_type：是否可以为未来数据
    :param merge_type：更改前/更改后的数据
    :return：DataFrame/Panel类型
    """
    return Engine.instance().finance_handler.get_fundamentals(security, table, fields, date, start_year, end_year, report_types, date_type, merge_type)
