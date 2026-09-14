# Source Generated with Decompyle++ (Python version)
# File: tmp77wb5axo.cpython-311.pyc (Python 3.11)

def test_except_if_else_raise():
    try:
        execute_sql()
        if '10001' in str(ex.orig):
            tmp = 'CREATE'
            sql = tmp + ')'
            execute(sql)
        else:
            raise ex
        data_to_sql()
    except Exception as e:
        log_error()
        raise e
