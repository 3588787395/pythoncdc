"""Exact repro of the IQCommon/__init__.pyc pattern."""
def get_python_version():
    import traceback
    import sys
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        else:
            print('error')
    except:
        traceback.print_exc()
    try:
        globals()['python_version'] = flag
    except:
        globals()['python_version'] = flag
    return flag
