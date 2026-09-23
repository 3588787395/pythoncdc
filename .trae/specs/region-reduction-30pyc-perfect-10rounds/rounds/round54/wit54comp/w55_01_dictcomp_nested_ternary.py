def w(stocks, delisting_set, ashares_list_local):
    return {stock: True if stock.replace('SZ', 'XSHE').replace('SS', 'XSHG') in delisting_set else (None if stock.replace('XSHE', 'SZ').replace('XSHG', 'SS') not in ashares_list_local else False) for stock in stocks}
