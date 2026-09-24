strategy_log = None


def t2(self, trans_direction, occur_balance, exchange_type):
    if exchange_type not in ('1', '2'):
        strategy_log.error('bad %s' % exchange_type)
        return False
    elif self.business_type != 'stock':
        strategy_log.error('stock only')
        return False
    else:
        kwargs = {'exchange_type': exchange_type, 'money_type': '0', 'occur_balance': occur_balance}
        error_dict, response = self.broker.trade_account.fund_transfer(**kwargs)
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
