# Source Generated with Decompyle++ (Python version)
# File: t2_utils.pyc (Python 3.11)

import datetime
from IQCommon.common import PTRADE_FUTURE_PATH, PTREDE_OPTION_PATH, PTRADE_PATH
from IQCommon.data.NetEngine import ConnectorManager
from IQCommon.logger import strategy_log
def do_request(function_id, **kwargs):
    account_type = kwargs.pop('account_type', 'PTRADE_INTERFACE')
    connector_manager = ConnectorManager()
    if account_type == 'PTRADE_FUTURE_INTERFACE':
        error_no, error_info = connector_manager.CreateConnector(1, PTRADE_FUTURE_PATH)
    elif account_type == 'PTRADE_OPTION_INTERFACE':
        error_no, error_info = connector_manager.CreateConnector(1, PTREDE_OPTION_PATH)
    elif account_type == 'PTRADE_INTERFACE':
        error_no, error_info = connector_manager.CreateConnector(1, PTRADE_PATH)
    else:
        return {'error_no': -1, 'error_info': '不支持的账户类型：%s' % account_type}
    if error_no != 0:
        strategy_log.error('创建T2连接失败，错误信息：%s' % error_info)
        return None
    else:
        response = []
        error_no, error_info = connector_manager.SendRcv(kwargs, function_id, response, 'PBOXQT1.0V%s' % datetime.datetime.now().strftime('%Y%m%d'))
        connector_manager.DestroyConnect()
        return ({'error_no': error_no, 'error_info': error_info}, response)
