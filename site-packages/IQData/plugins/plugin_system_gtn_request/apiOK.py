# Source Generated with Decompyle++ (Python version)
# File: api.pyc (Python 3.11)

from IQData.engine import Engine
from IQData.api.api_base import api_method
from IQData.enumerate import IQEnum
@api_method
def gtn_send_by_get(url, data):
    """
    用get请求方式从gtn获取数据
    :return:
    """
    return Engine.instance().request_handler.gtn_send_by_get(url, data)
@api_method
def gtn_send_by_post(url, data):
    """
    用post请求方式从gtn获取数据
    :return:
    """
    return Engine.instance().request_handler.gtn_send_by_post(url, data)
@api_method
def get_method_data(method, **kwargs):
    """
    获取指定数据服务中的数据
    :param method:    接口名称
    :param kwargs:    接口参数
    :return: pandas.DataFarme
    """
    if isinstance(method, IQEnum):
        method = method.value
    return Engine.instance().request_handler.send_service(method, **(kwargs))
