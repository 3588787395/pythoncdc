# Source Generated with Decompyle++ (Python version)
# File: iqdata_db_helper.pyc (Python 3.11)

from IQCommon.logger import system_log
from retrying import retry
from IQCommon.exception import get_traceback_message
class Engine(object):
    def __init__(self, db_name, db_type, db_config):
        self._Engine__db_url = self._Engine__get_config(db_name, db_type, db_config)
        self.engine = self._Engine__create_engine(self._Engine__db_url)
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_engine(self):
        try:
            return self.engine
        except Exception as e:
            system_log.error(get_traceback_message())
            raise e
    def __create_engine(self, db_url):
        import sqlalchemy
        from sqlalchemy.pool import NullPool
        kws = dict(poolclass=NullPool)
        try:
            eg = sqlalchemy.create_engine(db_url, **(kws))
            return eg
        except Exception as e:
            system_log.error('数据库连接创建失败， 连接信息为:{}'.format(db_url))
            raise Exception('数据库连接创建失败，请检查数据库连接信息及网络连接情况')
    def __get_config(self, db_name='jy', db_type='sql', db_config=None):
        _config = db_config
        if db_type == 'sql':
            if db_name is not None:
                db_url = f'mysql+pymysql://{_config.user!s}:{_config.passwd!s}@{_config.host!s}:{_config.port!s}/{_config.db!s}?charset={_config.charset!s}'
            else:
                system_log.error('没有获取到对应的数据库配置信息，请检查配置文件！')
                db_url = ''
            return db_url
        elif db_type == 'nosql':
            return None
