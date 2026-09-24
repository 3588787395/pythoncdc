strategy_log = None


def t4(self, trans_direction, exchange_type, occur_balance, error_dict):
    if error_dict.get('error_no') != 0:
        strategy_log.error(
            f"{'转入' if trans_direction == '0' else '转出'!s}失败"
            f"{error_dict.get('error_info')!s}")
        x = occur_balance
    return x
