# Source Generated with Decompyle++ (Python version)
# File: live_option_position.pyc (Python 3.11)

from abc import ABC
from IQEngine.account.base_position import BasePosition
from IQEngine.core.engine import Engine
from IQEngine.const import EntrustDirection, FuturesDirection, AccountType, OptionProperty, PositionType, HedgeType
from IQEngine.utils import check_price
from IQEngine.utils.exception import IQInvalidArgument
from IQEngine.utils.i18n import get_local_text as _
class LiveOptionPosition(ABC, BasePosition):
    def __init__(self, symbol):
        super(LiveOptionPosition, self).__init__(symbol)
        self._buy_holding_list = []
        self._sell_holding_list = []
        self._covered_holding_list = []
        self._buy_transaction_cost = 0.0
        self._sell_transaction_cost = 0.0
        self._covered_transaction_cost = 0.0
        self._buy_realized_pnl = 0.0
        self._sell_realized_pnl = 0.0
        self._covered_realized_pnl = 0.0
        self._buy_avg_open_price = 0.0
        self._sell_avg_open_price = 0.0
        self._covered_avg_open_price = 0.0
        self._buy_frozen_amount = 0
        self._sell_frozen_amount = 0
        self._covered_frozen_amount = 0
        self._buy_hold_pnl = 0
        self._sell_hold_pnl = 0
        self._covered_hold_pnl = 0
        self._margin = 0.0
        self._premium = 0.0
        self._hold_margin = None
        self._hold_premium = None
        self._type = None
        self._update_time = None
    def __repr__(self):
        return 'OptionPosition({})'.format(self.__dict__)
    def save(self):
        return None
    def load(self, state):
        return None
    def sync_position(self, position):
        self._buy_holding_list = []
        self._sell_holding_list = []
        self._covered_holding_list = []
        price = position['last_price']
        self._buy_holding_list.insert(0, (price, position['buy_amount']))
        self._sell_holding_list.insert(0, (price, position['sell_amount']))
        self._covered_holding_list.insert(0, (price, position['covered_amount']))
        self._buy_avg_open_price = position['buy_avg_price']
        self._sell_avg_open_price = position['sell_avg_price']
        self._covered_avg_open_price = position['covered_avg_price']
        self._buy_hold_pnl = position['buy_hold_pnl']
        self._sell_hold_pnl = position['sell_hold_pnl']
        self._covered_hold_pnl = position['covered_hold_pnl']
        self._buy_frozen_amount = position['buy_frozen_amount']
        self._sell_frozen_amount = position['sell_frozen_amount']
        self._covered_frozen_amount = position['covered_frozen_amount']
        self._type = position['position_type']
        self._hold_margin = position['hold_margin']
        self._hold_premium = position['hold_premium']
        self._update_time = position['update_time']
    @property
    def type(self):
        return AccountType.OPTION.value
    @property
    def option_property(self):
        return self.asset.option_property
    @property
    def position_type(self):
        return self._type
    @property
    def market_value(self):
        return self.buy_market_value - self.sell_market_value - self.covered_market_value
    @property
    def buy_market_value(self):
        return self.buy_amount * self.last_price * self.contract_multiplier
    @property
    def sell_market_value(self):
        return self.sell_amount * self.last_price * self.contract_multiplier
    @property
    def covered_market_value(self):
        return self.covered_amount * self.last_price * self.contract_multiplier
    @property
    def contract_multiplier(self):
        return self.asset.contract_multiplier
    @property
    def open_orders(self):
        return Engine.instance().algo.get_open_orders(self.symbol)
    @property
    def buy_holding_pnl(self):
        """
        [float] 权利仓持仓盈亏
        """
        return self._buy_hold_pnl
    @property
    def sell_holding_pnl(self):
        """
        [float] 非备兑义务仓持仓盈亏
        """
        return self._sell_hold_pnl
    @property
    def covered_holding_pnl(self):
        """
        [float] 备兑义务仓持仓盈亏
        """
        return self._covered_hold_pnl
    @property
    def buy_realized_pnl(self):
        """
        [float] 当日权利仓平仓盈亏，交易场景为0
        """
        return self._buy_realized_pnl
    @property
    def sell_realized_pnl(self):
        """
        [float] 当日非备兑义务仓平仓盈亏，交易场景为0
        """
        return self._sell_realized_pnl
    @property
    def covered_realized_pnl(self):
        """
        [float] 当日备兑义务仓平仓盈亏，交易场景为0
        """
        return self._covered_realized_pnl
    @property
    def holding_pnl(self):
        """
        [float] 合约总持仓盈亏
        """
        return self.buy_holding_pnl + self.sell_holding_pnl + self.covered_holding_pnl
    @property
    def realized_pnl(self):
        """
        [float] 当日合约总平仓盈亏，交易场景为0
        """
        return self.buy_realized_pnl + self.sell_realized_pnl + self.covered_realized_pnl
    @property
    def buy_daily_pnl(self):
        """
        [float] 当日权利仓总盈亏，交易场景即权利仓持仓盈亏
        """
        return self.buy_holding_pnl + self.buy_realized_pnl
    @property
    def sell_daily_pnl(self):
        """
        [float] 当日非备兑义务仓持仓总盈亏，交易场景即非备兑义务仓持仓盈亏
        """
        return self.sell_holding_pnl + self.sell_realized_pnl
    @property
    def covered_daily_pnl(self):
        """
        [float] 当日备兑义务仓持仓总盈亏，交易场景即非备兑义务仓持仓盈亏
        """
        return self.covered_holding_pnl + self.covered_realized_pnl
    @property
    def daily_pnl(self):
        """
        [float] 当日合约总盈亏，交易场景即当日合约总持仓盈亏
        """
        return self.holding_pnl + self.realized_pnl
    @property
    def buy_pnl(self):
        """
        [float] 买方向累计盈亏
        """
        return (self.last_price - self._buy_avg_open_price) * self.buy_amount * self.contract_multiplier
    @property
    def sell_pnl(self):
        """
        [float] 卖方向累计盈亏
        """
        return (self._sell_avg_open_price - self.last_price) * self.sell_amount * self.contract_multiplier
    @property
    def covered_pnl(self):
        """
        [float] 卖方向累计盈亏
        """
        return (self._covered_avg_open_price - self.last_price) * self.covered_amount * self.contract_multiplier
    @property
    def pnl(self):
        """
        [float] 累计盈亏
        """
        return self.buy_pnl + self.sell_pnl + self.covered_pnl
    @property
    def buy_amount(self):
        """
        [int] 买方向持仓
        """
        return sum((amount for price, amount in self._buy_holding_list))
    @property
    def sell_amount(self):
        """
        [int] 卖方向持仓
        """
        return sum((amount for price, amount in self._sell_holding_list))
    @property
    def covered_amount(self):
        """
        [int] 卖方向持仓
        """
        return sum((amount for price, amount in self._covered_holding_list))
    @property
    def margin(self):
        if self._hold_margin:
            return self._hold_margin
        else:
            return self._margin
    @property
    def premium(self):
        if self._hold_premium:
            return self._hold_premium
        else:
            return self._premium
    @property
    def buy_avg_holding_price(self):
        """
        [float] 权利仓持仓均价
        """
        return self._buy_avg_open_price
    @property
    def sell_avg_holding_price(self):
        """
        [float] 非备兑义务仓持仓均价
        """
        return self._sell_avg_open_price
    @property
    def covered_avg_holding_price(self):
        """
        [float] 备兑义务仓持仓均价
        """
        return self._covered_avg_open_price
    @property
    def buy_avg_open_price(self):
        return self._buy_avg_open_price
    @property
    def sell_avg_open_price(self):
        return self._sell_avg_open_price
    @property
    def covered_avg_open_price(self):
        return self._covered_avg_open_price
    @property
    def buy_transaction_cost(self):
        return self._buy_transaction_cost
    @property
    def sell_transaction_cost(self):
        return self._sell_transaction_cost
    @property
    def covered_transaction_cost(self):
        return self._covered_transaction_cost
    @property
    def transaction_cost(self):
        return self._buy_transaction_cost + self._sell_transaction_cost + self._covered_transaction_cost
    @property
    def exercise_date(self):
        return self.asset.exercise_date
    @property
    def update_time(self):
        """
        持仓更新时间
        """
        return self._update_time
    @property
    def _repr_attr_list(self):
        return ['type', 'position_type', 'market_value', 'buy_holding_pnl', 'sell_holding_pnl', 'covered_holding_pnl', 'holding_pnl', 'realized_pnl', 'buy_daily_pnl', 'sell_daily_pnl', 'covered_daily_pnl', 'daily_pnl', 'buy_pnl', 'sell_pnl', 'covered_pnl', 'pnl', 'buy_amount', 'sell_amount', 'covered_amount', 'margin', 'premium', 'buy_avg_holding_price', 'sell_avg_holding_price', 'covered_avg_holding_price', 'transaction_cost', 'exercise_date', 'last_price', 'contract_multiplier', 'update_time']
