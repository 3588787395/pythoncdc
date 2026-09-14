def create_transactions_stats_pattern(trades, positions):
    result = []
    for trade in trades:
        item = {}
        if len(positions) > 0:
            for pos in positions:
                if trade in pos.values():
                    multiplier = pos.get('multiplier')
                    item['multiplier'] = multiplier
                    if trade == 'OPEN':
                        if trade == 'BUY':
                            side = 'long'
                        else:
                            side = 'short'
                    elif trade == 'SELL':
                        side = 'long'
                    else:
                        side = 'short'
                    item['side'] = side
        result.append(item)
    return result
