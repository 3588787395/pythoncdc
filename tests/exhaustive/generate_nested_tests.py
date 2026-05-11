import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nested')

OUTER_TYPES = ['if', 'while', 'for', 'try', 'with', 'match']
INNER_TYPES = ['if', 'while', 'for', 'try', 'with', 'match', 'ternary', 'boolop']

VARIANTS = {
    'v1': {'cond': 'x', 'target': 'y', 'var_a': 'x', 'var_b': 'y', 'var_c': 'z',
           'loop_var': 'i', 'match_var': 'v'},
    'v2': {'cond': 'a', 'target': 'b', 'var_a': 'a', 'var_b': 'b', 'var_c': 'c',
           'loop_var': 'j', 'match_var': 'w'},
    'v3': {'cond': 'p', 'target': 'q', 'var_a': 'p', 'var_b': 'q', 'var_c': 'r',
           'loop_var': 'k', 'match_var': 'u'},
}

OUTER_CAP = {
    'if': 'If', 'while': 'While', 'for': 'For',
    'try': 'Try', 'with': 'With', 'match': 'Match',
}

INNER_CAP = {
    'if': 'If', 'while': 'While', 'for': 'For',
    'try': 'Try', 'with': 'With', 'match': 'Match',
    'ternary': 'Ternary', 'boolop': 'Boolop',
}


def inner_source(inner, ctx):
    c = ctx
    if inner == 'if':
        return 'if {cond}:\n    {target} = 1\nelse:\n    {target} = 2'.format(**c)
    elif inner == 'while':
        return 'while {cond}: {target} += 1'.format(**c)
    elif inner == 'for':
        return 'for {loop_var} in r: {target} += {loop_var}'.format(**c)
    elif inner == 'try':
        return 'try:\n    {target} = 1\nexcept:\n    {target} = 2'.format(**c)
    elif inner == 'with':
        return "with open('f') as f: {target} = f.read()".format(**c)
    elif inner == 'match':
        return 'match {match_var}:\n    case 1: {target} = 1\n    case _: {target} = 2'.format(**c)
    elif inner == 'ternary':
        return '{target} = {var_a} if {var_b} else {var_c}'.format(**c)
    elif inner == 'boolop':
        return '{target} = {var_a} and {var_b} and {var_c}'.format(**c)
    return 'pass'


def indent(text, n):
    prefix = '    ' * n
    return '\n'.join(prefix + line for line in text.split('\n'))


def make_source(outer, inner, ctx):
    isrc = inner_source(inner, ctx)

    if outer == 'if':
        return 'if {cond}:\n{body}'.format(cond=ctx['cond'], body=indent(isrc, 1))
    elif outer == 'while':
        return 'while {cond}:\n{body}'.format(cond=ctx['cond'], body=indent(isrc, 1))
    elif outer == 'for':
        return 'for {loop_var} in range(3):\n{body}'.format(
            loop_var=ctx['loop_var'], body=indent(isrc, 1))
    elif outer == 'try':
        return 'try:\n{body}\nexcept:\n    pass'.format(body=indent(isrc, 1))
    elif outer == 'with':
        return "with open('f') as f:\n{body}".format(body=indent(isrc, 1))
    elif outer == 'match':
        return 'match {match_var}:\n    case _:\n{body}'.format(
            match_var=ctx['match_var'], body=indent(isrc, 2))
    return ''


TEMPLATE = '''\
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class {class_name}(ExhaustiveTestCase):
    SOURCE_CODE = """{source_code}"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
'''


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    init_path = os.path.join(OUTPUT_DIR, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('')

    count = 0

    for outer in OUTER_TYPES:
        for inner in INNER_TYPES:
            for vkey, ctx in VARIANTS.items():
                source = make_source(outer, inner, ctx)

                outer_cap = OUTER_CAP[outer]
                inner_cap = INNER_CAP[inner]
                cls_name = 'TestNested{outer}{inner}_{variant}'.format(
                    outer=outer_cap, inner=inner_cap, variant=vkey)

                fname = 'test_nested_{outer}_{inner}_{variant}.py'.format(
                    outer=outer, inner=inner, variant=vkey)

                content = TEMPLATE.format(
                    class_name=cls_name,
                    source_code=source,
                )

                filepath = os.path.join(OUTPUT_DIR, fname)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                count += 1

    return count


if __name__ == '__main__':
    generated = main()
    print(f'Generated {generated} test files in: {OUTPUT_DIR}')

    sample = os.path.join(OUTPUT_DIR, 'test_nested_if_if_v1.py')
    if os.path.exists(sample):
        print('\nSample: test_nested_if_if_v1.py')
        print('=' * 60)
        with open(sample, 'r', encoding='utf-8') as f:
            print(f.read())

    print('\nAll generated files:')
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if fname.startswith('test_nested_') and fname.endswith('.py'):
            print(f'  {fname}')
