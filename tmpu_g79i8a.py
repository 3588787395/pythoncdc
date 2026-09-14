
def test_except_if_else_raise(self, table_name, data):
    from sqlalchemy.exc import OperationalError
    try:
        if isinstance(data, list):
            if not data:
                return None
            else:
                try:
                    data.append('x')
                except OperationalError as ex:
                    if '10001' in str(ex):
                        print('ok')
                        return None
                    else:
                        raise ex
        else:
            raise RuntimeError('bad')
    except Exception as e:
        print('err')
        raise e
