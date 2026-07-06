import os

EXHAUSTIVE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(EXHAUSTIVE_DIR, 'triple_nested')

OUTER_TYPES = ['if', 'while', 'for', 'try', 'with']
MID_TYPES = ['if', 'while', 'for', 'try']
INNER_TYPES = ['if', 'while', 'for']

VAR_SET_0 = {'outer': 'n', 'mid': 'm', 'inner': 'k'}
VAR_SET_1 = {'outer': 'x', 'mid': 'y', 'inner': 'z'}


def build_outer_open(otype, var):
    if otype == 'if':
        return f'if {var} > 0:', ''
    elif otype == 'while':
        return f'while {var} > 0:', f'    {var} -= 1'
    elif otype == 'for':
        return f'for {var} in range(10):', ''
    elif otype == 'try':
        return 'try:', 'except Exception:\n    pass'
    elif otype == 'with':
        return "with open('f') as f:", ''
    return '', ''


def build_mid_open(mtype, var):
    if mtype == 'if':
        return f'    if {var} > 0:', ''
    elif mtype == 'while':
        return f'    while {var} > 0:', f'        {var} -= 1'
    elif mtype == 'for':
        return f'    for {var} in range(5):', ''
    elif mtype == 'try':
        return '    try:', '    except Exception:\n        pass'
    return '', ''


def build_inner(itype, var):
    if itype == 'if':
        return f'        if {var} > 0:\n            {var} -= 1'
    elif itype == 'while':
        return f'        while {var} > 0:\n            {var} -= 1'
    elif itype == 'for':
        return f'        for {var} in range(3):\n            pass'
    return ''


def build_source(outer, mid, inner, vars_dict):
    o_open, o_close = build_outer_open(outer, vars_dict['outer'])
    m_open, m_close = build_mid_open(mid, vars_dict['mid'])
    i_code = build_inner(inner, vars_dict['inner'])

    lines = [o_open]
    lines.append(m_open)
    lines.append(i_code)
    if m_close:
        lines.append(m_close)
    if o_close:
        lines.append(o_close)

    return '\n'.join(lines)


def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    count = 0

    for outer in OUTER_TYPES:
        for mid in MID_TYPES:
            for inner in INNER_TYPES:
                for vi, vars_dict in enumerate([VAR_SET_0, VAR_SET_1]):
                    name = f'test_tn_{outer}_{mid}_{inner}_v{vi}'
                    class_name = f'TestTN_{outer.capitalize()}_{mid.capitalize()}_{inner.capitalize()}_v{vi}'
                    file_name = f'{name}.py'
                    file_path = os.path.join(OUTPUT_DIR, file_name)

                    source_code = build_source(outer, mid, inner, vars_dict)

                    content = f'''import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class {class_name}(ExhaustiveTestCase):
    SOURCE_CODE = """{source_code}"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
'''

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    count += 1

    return count


def main():
    print("=" * 60)
    print("三重嵌套穷举测试生成器")
    print("=" * 60)
    print(f"外层类型: {OUTER_TYPES}")
    print(f"中层类型: {MID_TYPES}")
    print(f"内层类型: {INNER_TYPES}")
    print(f"组合数: {len(OUTER_TYPES)} x {len(MID_TYPES)} x {len(INNER_TYPES)} x 2变体 = "
          f"{len(OUTER_TYPES) * len(MID_TYPES) * len(INNER_TYPES) * 2}")
    print(f"输出目录: {OUTPUT_DIR}")
    print()

    total = generate_all()

    print(f"\n总计生成 {total} 个测试文件到 {OUTPUT_DIR}")

    print("\n生成样本代码:")
    print("-" * 40)

    samples = [
        ('if', 'while', 'for', VAR_SET_0),
        ('for', 'if', 'while', VAR_SET_1),
        ('try', 'for', 'if', VAR_SET_0),
        ('while', 'try', 'for', VAR_SET_1),
        ('with', 'if', 'while', VAR_SET_0),
    ]

    for outer, mid, inner, vars_dict in samples:
        source = build_source(outer, mid, inner, vars_dict)
        print(f"\n[{outer} -> {mid} -> {inner}] vars={vars_dict}:")
        print(source)


if __name__ == '__main__':
    main()
