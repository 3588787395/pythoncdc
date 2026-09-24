strategy_log = None


def fund_transfer_case(self, trans_direction, occur_balance, exchange_type, error_dict):
    if error_dict.get('error_no') != 0:
        strategy_log.error(
            f"{'转入' if trans_direction == '0' else '转出'!s}极速"
            f"{'沪A' if exchange_type == '1' else '深A'!s}失败，错误原因："
            f"{error_dict.get('error_info')!s}")
        return False
    strategy_log.info(
        f"{'转入' if trans_direction == '0' else '转出'!s}极速"
        f"{'沪A' if exchange_type == '1' else '深A'!s}成功，入参金额："
        f"{occur_balance!s}")
    return True
