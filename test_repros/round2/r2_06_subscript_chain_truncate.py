"""Repro: get_last_stat subscript receiver chain truncation.

Original shape (4-level subscript chain feeding .append):
    result_data['data']['stat']['information']['value'].append(
        ([item[12 + index]] or [0])[0])

The decompiler emitted:
    'value'.append(([item[12 + index]] or [0] if item[12 + index] else [0])[0])
i.e. the whole receiver chain `result_data['data']['stat']['information']`
was dropped (leaving the bare string 'value') and the `[x] or [0]`
expression gained a spurious duplicated ternary. Several instructions
disappear and a JUMP_FORWARD appears.
"""


def get_last_stat(item, index):
    result_data = {'data': {'stat': {'information': {'time': [], 'value': []}}}}
    for i in range(index + 1):
        result_data['data']['stat']['information']['time'].append(i)
    result_data['data']['stat']['information']['value'].append(
        ([item[12 + index]] or [0])[0])
    result_data['data']['stat']['information']['value'].append(
        ([item[16 + index]] or [0])[0])
    return result_data
