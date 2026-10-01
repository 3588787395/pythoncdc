# Source Generated with Decompyle++ (Python version)
# File: r1_reg_get_daily_summary.pyc (Python 3.11)

import six
RunType = None
class PluginRiskCalculation:
    def get_daily_summary(self):
        if not self._daily_portfolios:
            return None
        self.current_days += 1
        summary = {'date': self._engine.trading_dt.date(), 'start_date': self._engine.config.strategy.start_date.strftime('%Y-%m-%d'), 'end_date': self._engine.config.strategy.end_date.strftime('%Y-%m-%d'), 'run_type': self._engine.config.strategy.run_type.value, 'benchmark': self._engine.config.strategy.benchmark}
        for account_type, starting_cash in six.iteritems(self._engine.config.strategy.accounts):
            summary[account_type] = starting_cash
        self.risk.set_daily_returns(self._portfolio_daily_returns, self._benchmark_daily_returns)
        total_return = self._safe_convert(self.risk.total_return)
        if self._engine.benchmark_portfolio:
            if self.config.strategy.run_type == RunType.TRADING:
                benchmark_annual_return = self._safe_convert(self._engine.benchmark_portfolio.benchmark_annualized_returns_trade)
            else:
                benchmark_annual_return = self._safe_convert(self._engine.benchmark_portfolio.benchmark_annualized_returns_backtest)
            benchmark_volatility = self._safe_convert(self.risk.benchmark_volatility)
        else:
            benchmark_annual_return = 0
            benchmark_volatility = 0
        risk_result = {'total_return': total_return, 'annual_return': self._safe_convert(self.risk.annual_return), 'benchmark_annual_return': benchmark_annual_return, 'alpha': self._safe_convert(self.risk.alpha), 'beta': self._safe_convert(self.risk.beta), 'sharp': self._safe_convert(self.risk.sharpe), 'sortino': self._safe_convert(self.risk.sortino), 'info_ratio': self._safe_convert(self.risk.info_ratio), 'algorithm_volatility': self._safe_convert(self.risk.algorithm_volatility), 'benchmark_volatility': benchmark_volatility, 'max_drawdown': self._safe_convert(self.risk.max_drawdown), 'daily_win_ratio': self._safe_convert(self.risk.daily_win_ratio), 'excess_return': self._safe_convert(self.risk.excess_return), 'excess_annual_return': self._safe_convert(self.risk.excess_annual_return)}
        if self.config.strategy.run_type == RunType.BACKTEST:
            risk_result['trade_win_ratio'] = self._safe_convert(self.risk.trade_win_ratio(self.trade_statistic['win_time'], self.trade_statistic['total_time']))
            risk_result['profit_loss_ratio'] = self._safe_convert(self.risk.profit_loss_ratio(self.trade_statistic['profit'], self.trade_statistic['loss']))
            risk_result['win_time'] = self._safe_convert(self.trade_statistic['win_time'])
            risk_result['lost_time'] = self._safe_convert(self.trade_statistic['lost_time'])
            risk_result['statistic_info'] = []
            risk_result['hold_days_info'] = 0
            risk_result['month_return'] = []
            risk_result['hold_ratio_mean'] = 0
        else:
            risk_result['trade_win_ratio'] = self._safe_convert(self.risk.trade_win_ratio(self.TradeMode_trade_statistic['win_time'], self.TradeMode_trade_statistic['total_time']))
            risk_result['profit_loss_ratio'] = self._safe_convert(self.risk.profit_loss_ratio(self.TradeMode_trade_statistic['profit'], self.TradeMode_trade_statistic['loss']))
            risk_result['win_time'] = self._safe_convert(self.TradeMode_trade_statistic['win_time'])
            risk_result['lost_time'] = self._safe_convert(self.TradeMode_trade_statistic['lost_time'])
            risk_result['statistic_info'] = []
            risk_result['hold_days_info'] = 0
            risk_result['month_return'] = []
            risk_result['hold_ratio_mean'] = 0
        self.risk.clear_data()
        if self.config.strategy.run_type == RunType.TRADING:
            self._orders = []
            self._daily_trades = []
        summary.update({'total_value': self._safe_convert(self._engine.portfolio.total_value), 'cash': self._safe_convert(self._engine.portfolio.cash), 'daily_pnl': self._safe_convert(self._engine.portfolio.daily_pnl), 'total_returns': self._safe_convert(self._engine.portfolio.total_returns), 'unit_net_value': self._safe_convert(self._engine.portfolio.unit_net_value), 'units': self._safe_convert(self._engine.portfolio.units), 'txn_count': len(self._trades), 'orders': self._orders, 'starting_cash': self.starting_cash, 'trading_days': self.trading_days, 'returns': total_return if len(self._returns) == 0 else self._safe_convert(total_return - self._returns[-1]) / (self._returns[-1] + 1), 'current_days': self.current_days, 'daily_orders': self._daily_orders})
        today = self._engine.calendar_dt.date()
        date = today
        self.daily_total_value_info[date] = self._safe_convert(self._engine.portfolio.total_value)
        self._returns.append(total_return)
        if self._engine.benchmark_portfolio:
            if self.config.strategy.run_type == RunType.BACKTEST:
                summary.update({'benchmark_total_returns': self._safe_convert(self._engine.benchmark_portfolio.total_returns_benchmark_backtest)})
            else:
                summary.update({'benchmark_total_returns': self._safe_convert(self._engine.benchmark_portfolio.total_returns_benchmark_trade)})
            summary.update({'benchmark_total_value': self._safe_convert(self._engine.benchmark_portfolio.total_value)})
        hold_ratio = round(self._daily_portfolios['market_value'] / self._daily_portfolios['total_value'], 4)
        self.hold_ratio_list.append(hold_ratio)
        self._daily_portfolios['hold_ratio'] = hold_ratio
        result_dict = {'summary': summary, 'trades': self._daily_trades, 'portfolio': self._daily_portfolios}
        if risk_result:
            result_dict.update({'risk_result': risk_result})
        if self._engine.benchmark_portfolio is not None:
            result_dict['benchmark_portfolio'] = self._daily_benchmark_portfolios
        for account_type, account in six.iteritems(self._engine.portfolio.accounts):
            result_dict['{}_account'.format(account_type)] = self._sub_accounts_daily[account_type]
            result_dict['{}_positions'.format(account_type)] = self._daily_positions[account_type]
        self._daily_orders = []
        self._daily_trades = []
        return result_dict
