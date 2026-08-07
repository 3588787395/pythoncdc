# Source Generated with Decompyle++ (Python version)
# File: accountFactory.pyc (Python 3.11)

ACCOUNT_TYPE_ENUM = {'PBOX_UFX_INTERFACE': 'PboxUFXAccount', 'PBOX_PT_INTERFACE': 'PboxPTAccount', 'PTRADE_INTERFACE': 'PtradeAccount', 'PTRADE_FUTURE_INTERFACE': 'PtradeFutureAccount', 'PTRADE_OPTION_INTERFACE': 'PtradeOptionAccount', 'PTRADE_HKS_INTERFACE': 'PtradeAccount'}
class AccountFactory(object):
    @staticmethod
    def create_account(account_type, op_station, trade_id=None, create_date='0', future_counter_type='UFT', channel_type=None):
        if account_type in ACCOUNT_TYPE_ENUM:
            if account_type == 'PBOX_UFX_INTERFACE':
                pass
            elif account_type == 'PBOX_PT_INTERFACE':
                pass
            elif account_type in ('PTRADE_INTERFACE', 'PTRADE_HKS_INTERFACE'):
                from fly.simtradding.ptradeAccount import PtradeAccount
            elif account_type == 'PTRADE_FUTURE_INTERFACE':
                from fly.simtradding.ptradeFutureAccount import PtradeFutureAccount
                return eval(ACCOUNT_TYPE_ENUM[account_type])(op_station=op_station, config_path=None, trade_id=trade_id, create_date=create_date, future_counter_type=future_counter_type)
            elif account_type == 'PTRADE_OPTION_INTERFACE':
                from fly.simtradding.ptradeOptionAccount import PtradeOptionAccount
            return eval(ACCOUNT_TYPE_ENUM[account_type])(op_station=op_station, config_path=None, trade_id=trade_id, create_date=create_date, channel_type=channel_type)
        else:
            raise KeyError
