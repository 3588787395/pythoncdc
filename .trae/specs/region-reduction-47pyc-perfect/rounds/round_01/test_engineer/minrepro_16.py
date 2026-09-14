def create_orders_stats_pattern(orders, positions):
    result = []
    for order in orders:
        item = {}
        if len(positions) > 0:
            for pos in positions:
                if order in pos.values():
                    item['multiplier'] = pos.get('multiplier')
                    if order == 'OPEN':
                        if order == 'BUY':
                            side = 'long'
                        else:
                            side = 'short'
                    elif order == 'BUY':
                        side = 'short'
                    else:
                        side = 'long'
                    item['side'] = side
        result.append(item)
    return result
