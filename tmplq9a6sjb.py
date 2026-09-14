
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
