# Source Generated with Decompyle++ (Python version)
# File: repro_12_isinstance_if_elif_return_in_try_except.cpython-311.pyc (Python 3.11)

def cancel_order(order_type, unit):
    try:
        request = {'unit': unit}
        if isinstance(unit, list):
            if order_type in ('stock', 'rzrq'):
                unit = unit[0]
                request['trade_unit'] = unit
            else:
                unit = unit[1]
                request['future_unit'] = unit
        elif order_type in ('stock', 'rzrq'):
            request['trade_unit'] = unit
        else:
            request['future_unit'] = unit
        if order_type == 'rzrq':
            return withdraw_rzrq(**(request))
        elif order_type == 'future':
            return withdraw_future(**(request))
        elif order_type == 'option':
            return withdraw_option(**(request))
        elif order_type == 'hks':
            return withdraw_hks(**(request))
        else:
            return withdraw_stock(**(request))
        return None
    except BaseException:
        error_msg = get_error()
        return {'error_no': -1, 'error_info': error_msg}
