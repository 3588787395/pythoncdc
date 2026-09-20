# -*- coding: utf-8 -*-
"""R13-J 复现（其二）：if/elif 链里某个分支的整块区域被旋转到了兄弟分支之后。

对应真实目标：
  IQEngine/plugins/plugin_system_matcher/matcher.pyc
      <module>.DefaultMatcher.match  [seq_len] orig=715 decomp=655

difflib 对齐（token 序列，公共前缀 165）：
   delete   orig#165-462 (298)  decomp#165-164 (0)
   delete   orig#575-578 (4)    decomp#277-276 (0)
   insert   orig#713-712 (0)    decomp#411-652 (242)
即：orig 在 #165 处的 `if order.entrust_direction == EntrustDirection.SELL and deal_price <=
get_limit_down(...): continue` 一整段（#165-181，实测 dis 1194..1318 之后 1322 JUMP_FORWARD->2464）
在反编译输出里被搬到了链尾（decomp#411 起，242 条）。也就是 matcherOK.py 里
`elif order.asset.symbol[:3] == '300':` 与 `elif self._price_limit:` 两支的相对次序被打乱。
"""


def match(self, order, deal_price, asset, EntrustDirection, trading_date, gem_change_date,
          stock_listed_date_str, is_first_five_trading_days, get_limit_up, get_limit_down,
          mark_cancelled, publish):
    while True:
        if not self._price_limit:
            if order.entrust_direction == EntrustDirection.BUY and deal_price >= get_limit_up(asset.symbol):
                continue
            if order.entrust_direction == EntrustDirection.SELL and deal_price <= get_limit_down(asset.symbol):
                continue
            if order.asset.symbol[:3] == '300':
                if not trading_date < gem_change_date:
                    if order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
                        if order.entrust_direction == EntrustDirection.BUY and deal_price >= get_limit_up(asset.symbol):
                            continue
                        if order.entrust_direction == EntrustDirection.SELL and deal_price <= get_limit_down(asset.symbol):
                            continue
            mark_cancelled('limit')
            publish()
            continue
        if self._price_limit:
            if order.entrust_direction == EntrustDirection.BUY and deal_price >= get_limit_up(asset.symbol):
                mark_cancelled('up')
                publish()
                continue
            if order.entrust_direction == EntrustDirection.SELL and deal_price <= get_limit_down(asset.symbol):
                mark_cancelled('down')
                publish()
                continue
        break
