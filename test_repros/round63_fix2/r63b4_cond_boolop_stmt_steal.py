# -*- coding: utf-8 -*-
"""R63-B4 合成复现：条件上下文 BoolOp 的「三元值块扩展」吞掉语句体首块与其后语句块。

对应语料缺陷：IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc
:: HistoryDataSource.get_kline_by_count（landed 854/841，丢 L625 三元 return 的
else 臂 + L628 cur_date 赋值 + L630 `if asset['type'] == 'FUTURE':` 测试）。

四个方法（Source 类）：
  1. cond_boolop_steals_stmt_block —— 见证形状：`if A or B:` 的链成员跳转目标是
     语句体首块（三元 return 的条件块，以 POP_JUMP_IF_NOT_NONE 结尾），链的落空
     目标是「赋值 + 紧随其后的 if 测试」同处一块的语句块（以 POP_JUMP_IF_FALSE
     结尾）。两块都以条件跳转结尾 ⇒ 被 P5 值块扩展误判为三元 true_value/false_value
     并吸进 BoolOpRegion.blocks，语句体与 if 之后的语句全部错位。
  2. cond_boolop_merge_test_terminated —— 同机制的第二形状：if 之后的语句块里
     放的是两条赋值 + `if count > 0:`（同样以条件跳转结尾），证明触发者是
     「以条件跳转结尾」这一结构事实而不是 FUTURE 测试本身。
  3. cond_boolop_merge_return_terminated —— 阴性对照 1：if 之后的语句块以
     RETURN_VALUE 结尾（不是条件跳转），扩展判据不成立 ⇒ 两臂都匹配，
     说明缺陷不是「if 后有语句」而是块尾形状。
  4. value_context_or_with_ternary —— 阴性对照 2：BoolOp 在**值上下文**
     （`x = A or (B if c else d)`），条件上下文判据不成立、扩展照旧生效 ⇒
     两臂都匹配，证明本候选没有砍掉 P5 扩展的本职用途。
"""

EMPTY = [1, 2, 3]


def convert_int_to_date(query_date):
    return query_date + 1


def get_pre_date(count, cur_date, frequency, trading_time=None):
    return (count, cur_date, frequency, trading_time)


def set_params_to_kwargs(asset, first, second, frequency):
    return (first, second, frequency, len(asset))


class Handler:

    def get_security_info(self, symbol):
        return {symbol: {'type': 'FUTURE', 'trading_time': 9}}


class Engine:

    def __init__(self):
        self.basic_data_handler = Handler()


class Source:

    def __init__(self):
        self.engine = Engine()

    def cond_boolop_steals_stmt_block(self, symbol, count, query_date, frequency,
                                      fields=None):
        asset = self.engine.basic_data_handler.get_security_info(symbol)[symbol]
        if len(asset) < 1 or count == 0:
            return EMPTY if fields is None else EMPTY[fields]
        cur_date = convert_int_to_date(query_date)
        if asset['type'] == 'FUTURE':
            pre_date = get_pre_date(count, cur_date, frequency, asset['trading_time'])
        else:
            pre_date = get_pre_date(count, cur_date, frequency)
        if count > 0:
            params = set_params_to_kwargs(asset, pre_date, cur_date, frequency)
        else:
            params = set_params_to_kwargs(asset, cur_date, pre_date, frequency)
        return params

    def cond_boolop_merge_test_terminated(self, symbol, count, query_date, frequency,
                                          fields=None):
        asset = self.engine.basic_data_handler.get_security_info(symbol)[symbol]
        if len(asset) < 1 or count == 0:
            return EMPTY if fields is None else EMPTY[fields]
        cur_date = convert_int_to_date(query_date)
        pre_date = get_pre_date(count, cur_date, frequency)
        if count > 0:
            params = set_params_to_kwargs(asset, pre_date, cur_date, frequency)
        else:
            params = set_params_to_kwargs(asset, cur_date, pre_date, frequency)
        return params

    def cond_boolop_merge_return_terminated(self, symbol, count, query_date,
                                           frequency, fields=None):
        asset = self.engine.basic_data_handler.get_security_info(symbol)[symbol]
        if len(asset) < 1 or count == 0:
            return EMPTY if fields is None else EMPTY[fields]
        cur_date = convert_int_to_date(query_date)
        return set_params_to_kwargs(asset, cur_date, query_date, frequency)

    def value_context_or_with_ternary(self, flag, other, third, chosen=None):
        asset = self.engine.basic_data_handler.get_security_info(flag)[flag]
        picked = (len(asset) < 1) or (other if third else chosen)
        if picked:
            return 1
        return 0
