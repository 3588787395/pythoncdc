# -*- coding: utf-8 -*-
"""Round 68 diag5 synthetic witness W1 (root cause: region_analyzer L19688
`_then_exit_succs = set(then_blocks[0].successors)` takes the then-arm's FIRST
block successors -- an *internal* edge when the arm contains a nested region --
while the elif arms use `_body[-1].successors`.  With every elif arm and the
final else terminating in RETURN_VALUE, the single non-empty "exit" is that
internal edge, it is adopted as the chain merge, and the then arm is then
re-collected bounded by its own interior block: everything after the nested
try/except in the then arm disappears from the AST."""


def params_analysis(filter_type, value, value_params):
    if filter_type in ('up_v', 'down_v'):
        try:
            value = value[-1]
        except Exception:
            value = value
        return {'filter_type': filter_type, 'value': value,
                'ob_value': float(value_params)}
    elif filter_type == 'region_v':
        try:
            value = value[-1]
        except Exception:
            value = value
        value_params = value_params.split(',')
        return {'filter_type': filter_type, 'value': value,
                'ob_start_value': float(value_params[0]),
                'ob_end_value': float(value_params[1])}
    elif filter_type == 'up_mean':
        return {'filter_type': filter_type, 'value_array': value,
                'ob_days': int(value_params)}
    else:
        return {'filter_type': filter_type, 'value': value}
