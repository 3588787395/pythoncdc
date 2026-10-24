# Source Generated with Decompyle++ (Python version)
# File: api_db.pyc (Python 3.11)

from IQData.plugins.plugin_system_db.iqdata_db_base import DataBaseManager
from IQCommon.exception import get_traceback_message
from IQCommon.logger import system_log
def get_db(db_name, db_type='sql'):
    """
    获取指定数据库类对象
    :param db_name: 数据库名
    :param db_type: 数据库类型, sql 或 nosql
    :return: DataBase类对象
    """
    try:
        from IQData.engine import Engine
        _config = getattr(Engine.instance().config.plugins.plugin_system_db, db_name, 'jy')
        return DataBaseManager.instance().get_or_create_db(db_name=db_name, db_type=db_type, db_config=_config)
    except Exception as e:
        system_log.error(get_traceback_message())
        raise e
func_list = ['get_db']
