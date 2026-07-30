# Source Generated with Decompyle++ (Python version)
# File: base_storage.pyc (Python 3.11)

from IQCommon.util.pycompatibility import lru_cache
class BaseStorage(object):
    @lru_cache()
    def __new__(cls, path):
        return super(BaseStorage, cls).__new__(cls)
    @classmethod
    def cache_clear(cls):
        cls.__new__.cache_clear()
    @classmethod
    def cache_info(cls):
        return cls.__new__.cache_info()
