# Source Generated with Decompyle++ (Python version)
# File: live_hks_position.pyc (Python 3.11)

from IQEngine.const import AccountType, EntrustDirection, PositionType, t0_symbol_set
from IQEngine.core.engine import Engine
from IQCommon.logger import system_log
from IQEngine.account.base_position import BasePosition
from IQEngine.utils.exception import IQInvalidArgument
from IQEngine.utils.i18n import get_local_text as _
class LiveHksPosition(BasePosition):
    def __init__(self, symbol):
        super(LiveHksPosition, self).__init__(symbol)
        self._enable_amount = 0
        self._amount = 0
        self._update_time = None
    def __repr__(self):
        return 'HksPosition({})'.format(self.__dict__)
    def save(self):
        return None
    def load(self, state):
        return None
    def sync_position(self, position):
        self._amount = position['amount']
        self._avg_price = position['avg_price']
        self._non_closable = position['today_amount']
        self._frozen = position['frozen_amount']
        self._transaction_cost = position['transaction_cost']
        self._enable_amount = position['enable_amount']
        self._income_balance = position['income_balance']
        self._hks_market_value = position['hks_market_value']
        self._update_time = position['update_time']
    @property
    def type(self):
        return AccountType.HKS.value
    @property
    def market_value(self):
        """
        持仓市值
        :return:
        """
        return self._amount * self.last_price
    @property
    def today_amount(self):
        """
        [int] 股票今日买入数量
        """
        return self._non_closable
    @property
    def sellable(self):
        return self._enable_amount
    @property
    def amount(self):
        """
        [int] 当前持仓股数
        """
        return self._amount
    @property
    def avg_price(self):
        """
        [float] 获得该持仓的买入均价，计算方法为每次买入的数量做加权平均
        """
        return self._avg_price
    @property
    def hks_market_value(self):
        """
        [float] 港股通持仓市值
        """
        return self._hks_market_value
    @property
    def update_time(self):
        """
        更新时间
        """
        return self._update_time
    @property
    def _repr_attr_list(self):
        return ['type', 'market_value', 'today_amount', 'sellable', 'amount', 'avg_price', 'hks_market_value', 'update_time']
