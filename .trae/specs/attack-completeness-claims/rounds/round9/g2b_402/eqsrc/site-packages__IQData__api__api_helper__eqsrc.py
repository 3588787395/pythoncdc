# Source Generated with Decompyle++ (Python version)
# File: api_helper.pyc (Python 3.11)

from IQData.api import api_base, api_extra
from IQData.utils.function_dict import FuncDict
def get_api():
    api_dict = FuncDict({name: getattr(api_base, name) for name in api_base.__all__})
    return api_dict
def extra_release():
    api_extra.clear_all_extra_api()
