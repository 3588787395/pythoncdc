# Source Generated with Decompyle++ (Python version)
# File: zt_api.pyc (Python 3.11)

from IQCommon.strategy.hg_api import factor_info_get, write_file, read_file, entrust_risk_info_get, read_order_csv, backtest_entrust_risk_info_get
def read_model_file(model):
    sys_config = dict()
    sys_config['model_id'] = model['model_id']
    sys_config['change_percent'] = float(model['change_ratio']) * 0.01
    sys_config['change_percent_up'] = float(model['change_ratio_high']) * 0.01
    sys_config['change_percent_down'] = float(model['change_ratio_low']) * 0.01
    sys_config['trunover_days'] = int(model['turnover_days'])
    sys_config['trunover_avg_percent'] = float(model['turnover_avg'])
    sys_config['pe'] = float(model['pe_times'])
    sys_config['pb'] = float(model['pb_times'])
    sys_config['price'] = float(model['close'])
    sys_config['price5'] = float(model['close_ma5'])
    sys_config['price10'] = float(model['close_ma10'])
    sys_config['price20'] = float(model['close_ma20'])
    sys_config['price30'] = float(model['close_ma30'])
    sys_config['price60'] = float(model['close_ma60'])
    sys_config['price120'] = float(model['close_ma120'])
    sys_config['close_percent1'] = float(sys_config['price5'] / sys_config['price'])
    sys_config['close_percent2'] = float(sys_config['price10'] / sys_config['price'])
    sys_config['close_percent3'] = float(sys_config['price20'] / sys_config['price'])
    sys_config['close_percent4'] = float(sys_config['price30'] / sys_config['price'])
    sys_config['close_percent5'] = float(sys_config['price60'] / sys_config['price'])
    sys_config['close_percent6'] = float(sys_config['price120'] / sys_config['price'])
    sys_config['close_percent_up1'] = float(model['close_ma5_high']) * 0.01
    sys_config['close_percent_up2'] = float(model['close_ma10_high']) * 0.01
    sys_config['close_percent_up3'] = float(model['close_ma20_high']) * 0.01
    sys_config['close_percent_up4'] = float(model['close_ma30_high']) * 0.01
    sys_config['close_percent_up5'] = float(model['close_ma60_high']) * 0.01
    sys_config['close_percent_up6'] = float(model['close_ma120_high']) * 0.01
    sys_config['close_percent_down1'] = float(model['close_ma5_low']) * 0.01
    sys_config['close_percent_down2'] = float(model['close_ma10_low']) * 0.01
    sys_config['close_percent_down3'] = float(model['close_ma20_low']) * 0.01
    sys_config['close_percent_down4'] = float(model['close_ma30_low']) * 0.01
    sys_config['close_percent_down5'] = float(model['close_ma60_low']) * 0.01
    sys_config['close_percent_down6'] = float(model['close_ma120_low']) * 0.01
    sys_config['stock_avg_poly1'] = int(model['indiv_ma5_up'])
    sys_config['stock_avg_poly2'] = int(model['indiv_ma10_up'])
    sys_config['stock_avg_poly3'] = int(model['indiv_ma20_up'])
    sys_config['stock_avg_poly4'] = int(model['indiv_ma30_up'])
    sys_config['stock_avg_poly5'] = int(model['indiv_ma60_up'])
    sys_config['stock_avg_poly6'] = int(model['indiv_ma120_up'])
    sys_config['industry_avg_poly1'] = int(model['indus_ma5_up'])
    sys_config['industry_avg_poly2'] = int(model['indus_ma10_up'])
    sys_config['industry_avg_poly3'] = int(model['indus_ma20_up'])
    sys_config['industry_avg_poly4'] = int(model['indus_ma30_up'])
    sys_config['industry_avg_poly5'] = int(model['indus_ma60_up'])
    sys_config['industry_avg_poly6'] = int(model['indus_ma120_up'])
    return sys_config
def read_config_file(factor_id, num, is_trade_flag):
    factor_type = 0
    info = factor_info_get(factor_id, factor_type)
    sys_config = read_model_file(info[0])
    factor_type = 1
    info = factor_info_get(factor_id, factor_type)
    sys_config['pe_times_low'] = float(info[0].get('pe_times_low', -999999))
    sys_config['pe_times_high'] = float(info[0].get('pe_times_high', info[0].get('pe_times', 0)))
    sys_config['pb_times_low'] = float(info[0].get('pb_times_low', -999999))
    sys_config['pb_times_high'] = float(info[0].get('pb_times_high', info[0].get('pb_times', 0)))
    sys_config['circulation'] = float(info[0]['circulation'])
    sys_config['dividend_ratio'] = float(info[0]['dividend_ratio'])
    sys_config['circulation_low'] = float(info[0]['circulation_low'])
    sys_config['growing_forecast'] = float(info[0]['growing_forecast'])
    sys_config['transfer_ratio'] = float(info[0]['transfer_ratio'])
    sys_config['total_value_low'] = float(info[0].get('total_value_low', info[0].get('total_value', 0)))
    sys_config['total_value_high'] = float(info[0].get('total_value_high', -999999))
    sys_config['roe'] = float(info[0]['roe'])
    if is_trade_flag:
        sys_config['factor_name'] = info[0]['factor_name']
    factor_type = 2
    info = factor_info_get(factor_id, factor_type)
    sys_config['indus_ma5_up'] = float(info[0]['indus_ma5_up'])
    sys_config['indus_ma10_up'] = float(info[0]['indus_ma10_up'])
    sys_config['indus_ma20_up'] = float(info[0]['indus_ma20_up'])
    sys_config['indus_ma30_up'] = float(info[0]['indus_ma30_up'])
    sys_config['indus_ma60_up'] = float(info[0]['indus_ma60_up'])
    sys_config['indus_ma120_up'] = float(info[0]['indus_ma120_up'])
    factor_type = 3
    info = factor_info_get(factor_id, factor_type)
    sys_config['buy_point'] = float(info[0]['buy_refer_ratio']) * 0.01
    sys_config['stop_loss'] = float(info[0]['loss_refer_ratio']) * 0.01
    sys_config['take_profit'] = float(info[0]['profit_refer_ratio']) * 0.01
    sys_config['capital_use_ratio'] = float(info[0]['capital_use_ratio'])
    sys_config['capital_of_per_share'] = float(info[0]['capital_of_per_share'])
    sys_config['max_position'] = int(info[0]['max_position'])
    sys_config['capital_of_transaction'] = float(info[0]['capital_of_transaction'])
    try:
        sys_config['hold_days'] = int(info[0]['hold_days'])
    except:
        sys_config['hold_days'] = 10
    return sys_config
def amount_trans(stock, amount):
    if stock[:2] == '68':
        if amount < 200:
            return 0
        else:
            return int(amount)
    elif stock[:2] in ('11', '10', '12'):
        amount = int(amount / 10) * 10
    else:
        amount = int(amount / 100) * 100
    return amount
