"""R27 测试工程师：渐进式复现share_change的AND链识别失败，找出导致失败的上下文因素"""
import os
import sys
import dis
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_27/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

# 渐进式添加上下文，找出导致AND链识别失败的 factor
CASES = [
    # 基准：纯if-elif链（已知通过）
    ('repro_r27_ctx_00_base',
     'def f(start_year, end_year, params):\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'),

    # 添加默认参数
    ('repro_r27_ctx_01_defaults',
     'def f(security, start_year=None, end_year=None, fields=None):\n'
     '    params = {}\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'),

    # 添加后续代码
    ('repro_r27_ctx_02_after_code',
     'def f(start_year, end_year, params):\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'
     '    x = 1\n'),

    # 添加前置代码
    ('repro_r27_ctx_03_before_code',
     'def f(start_year, end_year, params):\n'
     '    security = str(start_year)\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'),

    # 添加后续if语句
    ('repro_r27_ctx_04_after_if',
     'def f(start_year, end_year, params, fields):\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'
     '    if fields is not None:\n'
     '        params[\'fields\'] = fields\n'),

    # 最接近share_change的结构
    ('repro_r27_ctx_05_full_context',
     'def f(security, start_year=None, end_year=None, fields=None):\n'
     '    return_data = {}\n'
     '    return_data[\'data\'] = []\n'
     '    params = {\'page_no\': \'1\'}\n'
     '    security = str(security)\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'
     '    if fields is not None:\n'
     '        fields = str(fields)\n'
     '        params[\'fields\'] = fields\n'
     '    max_stocks_num = 400\n'
     '    return params\n'),

    # 只有后续if(fields is not None)不带else
    ('repro_r27_ctx_06_trailing_if_none',
     'def f(start_year, end_year, params, fields):\n'
     '    if start_year is not None and end_year is None:\n'
     '        params[\'start_year\'] = start_year\n'
     '    elif start_year is None and end_year is not None:\n'
     '        params[\'end_year\'] = end_year\n'
     '    elif start_year is not None and end_year is not None:\n'
     '        params[\'start_year\'] = start_year\n'
     '        params[\'end_year\'] = end_year\n'
     '    if fields is not None:\n'
     '        pass\n'),
]


def main():
    from pycdc import decompile_pyc

    results = []
    for name, src in CASES:
        src_path = os.path.join(OUT_DIR, name + '.py')
        pyc_path = os.path.join(OUT_DIR, name + '.pyc')
        dec_path = os.path.join(OUT_DIR, name + '_decompiled.py')

        with open(src_path, 'w', encoding='utf-8') as f:
            f.write(src)
        py_compile.compile(src_path, pyc_path, doraise=True)

        try:
            dec_src = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
            with open(dec_path, 'w', encoding='utf-8') as f:
                f.write(dec_src)
        except Exception as e:
            results.append((name, 'DECOMPILE_ERROR', str(e)[:80], ''))
            continue

        orig_co = compile(src, '<orig>', 'exec')
        dec_co = compile(dec_src, '<dec>', 'exec')

        def get_f_instrs(co):
            for c in co.co_consts:
                if isinstance(c, type(co)) and c.co_name == 'f':
                    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(c)
                            if i.opname not in ('EXTENDED_ARG', 'CACHE', 'RESUME', 'NOP')]
            return []

        orig_instrs = get_f_instrs(orig_co)
        dec_instrs = get_f_instrs(dec_co)

        if orig_instrs == dec_instrs:
            results.append((name, 'PASS', f'{len(orig_instrs)} instrs', ''))
        else:
            min_len = min(len(orig_instrs), len(dec_instrs))
            first_diff = -1
            for i in range(min_len):
                if orig_instrs[i] != dec_instrs[i]:
                    first_diff = i
                    break
            if first_diff == -1 and len(orig_instrs) != len(dec_instrs):
                first_diff = min_len
            detail = ''
            if first_diff < min_len:
                o = orig_instrs[first_diff]
                d = dec_instrs[first_diff]
                detail = f'idx={first_diff}: {o[1]} {o[2]} -> {d[1]} {d[2]}'
            else:
                detail = f'len: {len(orig_instrs)} -> {len(dec_instrs)}'
            # 也显示反编译后的源码前几行
            dec_lines = dec_src.split('\n')
            src_preview = ' | '.join(l.strip() for l in dec_lines[3:8] if l.strip())
            results.append((name, 'FAIL', detail, src_preview[:80]))

    print(f"=== R27 渐进式复现 ({len(results)} 个) ===")
    for name, status, detail, preview in results:
        marker = '✓' if status == 'PASS' else '✗'
        print(f"  {marker} {name:<40} {status:<15} {detail}")
        if preview:
            print(f"     src: {preview}")


if __name__ == '__main__':
    main()
