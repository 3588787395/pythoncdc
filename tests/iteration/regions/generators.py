import random
import json
import os
from typing import List, Dict, Any, Optional


BASIC = 'basic'
MODERATE = 'moderate'
ADVANCED = 'advanced'
ADVERSARIAL = 'adversarial'


def complexity_for_round(round_num: int) -> str:
    if round_num <= 5:
        return BASIC
    elif round_num <= 10:
        return MODERATE
    elif round_num <= 15:
        return ADVANCED
    else:
        return ADVERSARIAL


class PatternGenerator:
    region_type: str = 'base'

    def __init__(self, seed: int = 42, complexity: str = BASIC,
                 regression_seeds: Optional[List[str]] = None):
        self.rng = random.Random(seed)
        self.complexity = complexity
        self.regression_seeds = regression_seeds or []
        self._seed_idx = 0

    def _var(self, pool: str = 'xyzwv') -> str:
        return self.rng.choice(pool)

    def _int(self, lo: int = 0, hi: int = 9) -> int:
        return self.rng.randint(lo, hi)

    def _bool(self) -> bool:
        return self.rng.choice([True, False])

    def _choose(self, options):
        return self.rng.choice(options)

    def _stmt_assign(self, indent: str = '') -> str:
        v = self._var()
        val = self._int()
        return f'{indent}{v} = {val}'

    def _stmt_call(self, indent: str = '') -> str:
        fname = f'f{self._int(0,9)}'
        arg = self._int()
        return f'{indent}{fname}({arg})'

    def _stmt_call_assign(self, indent: str = '') -> str:
        v = self._var()
        return f'{indent}g({self._int()})\n{indent}{v} = {self._int()}'

    def _body_stmts(self, n: int, indent: str = '    ') -> List[str]:
        stmts = []
        for _ in range(n):
            kind = self._choose(['assign', 'call', 'call_assign'])
            if kind == 'assign':
                stmts.append(self._stmt_assign(indent))
            elif kind == 'call':
                stmts.append(self._stmt_call(indent))
            else:
                stmts.append(self._stmt_call_assign(indent))
        return stmts

    def generate(self, count: int) -> List[str]:
        patterns = []
        if self.complexity == ADVERSARIAL and self.regression_seeds:
            for seed in self.regression_seeds[:count]:
                patterns.append(seed)
            self._seed_idx = len(patterns)
            remaining = count - len(patterns)
        else:
            remaining = count
        for _ in range(remaining):
            patterns.append(self._generate_one())
        return patterns

    def _generate_one(self) -> str:
        raise NotImplementedError


class IfGenerator(PatternGenerator):
    region_type = 'if'

    def _generate_one(self) -> str:
        v = self._var()
        n = self._int()
        has_else = self._bool()
        n_body = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
        body = '\n'.join(self._body_stmts(n_body))
        result = f'if {v}:\n{body}'
        if has_else:
            n_else = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
            else_body = '\n'.join(self._body_stmts(n_else, '    '))
            result += f'\nelse:\n{else_body}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            has_elif = self._bool()
            if has_elif:
                n_elif = self.rng.randint(1, 2)
                for _ in range(n_elif):
                    ev = self._var('abc')
                    en = self._int()
                    elif_body = '\n'.join(self._body_stmts(
                        self.rng.randint(1, 2), '    '))
                    result += f'\nelif {ev}:\n{elif_body}'
        if self.complexity in (ADVANCED, ADVERSARIAL):
            has_nested = self._bool()
            if has_nested:
                nv = self._var('abc')
                inner = f'if {nv}:\n' + '\n'.join(self._body_stmts(1, '    '))
                result = result.replace('if ', f'{inner}\nif ', 1) if self._bool() else result
        return result


class LoopGenerator(PatternGenerator):
    region_type = 'loop'

    def _generate_one(self) -> str:
        kind = self._choose(['for', 'while'])
        if kind == 'for':
            v = self._var()
            hi = self._int(1, 5)
            header = f'for {v} in range({hi}):'
        else:
            cond = self._var()
            header = f'while {cond}:'
        n_body = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
        body = '\n'.join(self._body_stmts(n_body, '    '))
        result = f'{header}\n{body}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            has_else = self._bool()
            if has_else:
                else_body = '\n'.join(self._body_stmts(1, '    '))
                result += f'\nelse:\n{else_body}'
        if self.complexity in (ADVANCED, ADVERSARIAL):
            has_break = self._bool()
            if has_break and 'for' in header:
                result += '\n    if x:\n        break'
        return result


class WithGenerator(PatternGenerator):
    region_type = 'with'

    def _generate_one(self) -> str:
        v = self._var()
        has_as = self._bool()
        n_body = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
        body = '\n'.join(self._body_stmts(n_body, '    '))
        if has_as:
            result = f'with {v} as ctx:\n{body}'
        else:
            result = f'with {v}:\n{body}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            multi = self._bool()
            if multi:
                v2 = self._var('abc')
                result = f'with {v} as c1, {v2} as c2:\n{body}'
        return result


class TryExceptGenerator(PatternGenerator):
    region_type = 'tryexcept'

    EXC_TYPES = ['ValueError', 'TypeError', 'IndexError', 'KeyError',
                 'RuntimeError', 'OSError', 'AttributeError', 'ZeroDivisionError']

    def _generate_one(self) -> str:
        handlers = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
        has_else = self._bool()
        has_finally = self._bool()
        n_try = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
        try_stmts = []
        for _ in range(n_try):
            kind = self._choose(['assign', 'call', 'call_assign'])
            if kind == 'assign':
                try_stmts.append(self._stmt_assign())
            elif kind == 'call':
                try_stmts.append(self._stmt_call())
            else:
                try_stmts.append(self._stmt_call_assign())
        lines = ['try:']
        lines.extend(f'    {s}' for s in try_stmts)
        bare_used = False
        for h in range(handlers):
            n_h = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
            handler_stmts = []
            for _ in range(n_h):
                kind = self._choose(['assign', 'call', 'call_assign'])
                if kind == 'assign':
                    handler_stmts.append(self._stmt_assign())
                elif kind == 'call':
                    handler_stmts.append(self._stmt_call())
                else:
                    handler_stmts.append(self._stmt_call_assign())
            use_bare = self._bool() and (h == handlers - 1)
            if use_bare:
                lines.append('except:')
                bare_used = True
            else:
                lines.append(f'except {self._choose(self.EXC_TYPES)}:')
            lines.extend(f'    {s}' for s in handler_stmts)
        if has_else:
            lines.append('else:')
            for _ in range(self.rng.randint(1, 2)):
                lines.append(f'    {self._stmt_assign()}')
        if has_finally:
            lines.append('finally:')
            for _ in range(self.rng.randint(1, 2)):
                lines.append(f'    {self._stmt_assign()}')
        return '\n'.join(lines)


class MatchGenerator(PatternGenerator):
    region_type = 'match'

    def _generate_one(self) -> str:
        v = self._var()
        n_cases = self.rng.randint(2, 4 if self.complexity != BASIC else 2)
        has_wildcard = self._bool() if n_cases > 1 else False
        lines = [f'match {v}:']
        for c in range(n_cases):
            body_stmts = []
            n = self.rng.randint(1, 3 if self.complexity != BASIC else 1)
            for _ in range(n):
                kind = self._choose(['assign', 'call', 'call_assign'])
                if kind == 'assign':
                    body_stmts.append(self._stmt_assign('        '))
                elif kind == 'call':
                    body_stmts.append(self._stmt_call('        '))
                else:
                    body_stmts.append(self._stmt_call_assign('        '))
            if c == n_cases - 1 and has_wildcard:
                lines.append('    case _:')
            else:
                val = self._int(0, 9)
                lines.append(f'    case {val}:')
            lines.extend(body_stmts)
        if self.complexity in (ADVANCED, ADVERSARIAL):
            use_string = self._bool()
            if use_string:
                lines.insert(1, f'    case "hello":')
                lines.insert(2, '        a = 1')
        return '\n'.join(lines)


class AssertGenerator(PatternGenerator):
    region_type = 'assert'

    def _generate_one(self) -> str:
        v = self._var()
        has_msg = self._bool()
        if self.complexity == BASIC:
            if has_msg:
                return f'assert {v}, "msg"'
            return f'assert {v}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            cmp_kind = self._choose(['simple', 'compare', 'boolop'])
            if cmp_kind == 'simple':
                expr = v
            elif cmp_kind == 'compare':
                expr = f'{v} > {self._int()}'
            else:
                expr = f'{v} and {self._var("abc")}'
            if has_msg:
                return f'assert {expr}, "msg"'
            return f'assert {expr}'
        return f'assert {v}'


class BoolOpGenerator(PatternGenerator):
    region_type = 'boolop'

    def _generate_one(self) -> str:
        v1 = self._var('xyz')
        v2 = self._var('abc')
        v3 = self._var('def')
        op = self._choose(['and', 'or'])
        if self.complexity == BASIC:
            return f'if {v1} {op} {v2}:\n    {v3} = {self._int()}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            n_terms = self.rng.randint(2, 4)
            terms = [self._var('abcdefgh') for _ in range(n_terms)]
            op2 = self._choose(['and', 'or'])
            expr = f' {op2} '.join(terms)
            body = '\n'.join(self._body_stmts(self.rng.randint(1, 2), '    '))
            return f'if {expr}:\n{body}'
        return f'if {v1} {op} {v2}:\n    {v3} = {self._int()}'


class TernaryGenerator(PatternGenerator):
    region_type = 'ternary'

    def _generate_one(self) -> str:
        v = self._var()
        if self.complexity == BASIC:
            return f'{v} = {self._int()} if {self._var("abc")} else {self._int(5,9)}'
        if self.complexity in (MODERATE, ADVANCED, ADVERSARIAL):
            cond_kind = self._choose(['simple', 'compare', 'boolop'])
            if cond_kind == 'simple':
                cond = self._var('abc')
            elif cond_kind == 'compare':
                cond = f'{self._var("abc")} > {self._int()}'
            else:
                cond = f'{self._var("abc")} and {self._var("def")}'
            true_val = self._int()
            false_val = self._int(5, 9)
            return f'{v} = {true_val} if {cond} else {false_val}'
        return f'{v} = {self._int()} if {self._var("abc")} else {self._int(5,9)}'


GENERATOR_MAP = {
    'if': IfGenerator,
    'loop': LoopGenerator,
    'with': WithGenerator,
    'tryexcept': TryExceptGenerator,
    'match': MatchGenerator,
    'assert': AssertGenerator,
    'boolop': BoolOpGenerator,
    'ternary': TernaryGenerator,
}

REGION_ORDER = ['if', 'loop', 'with', 'tryexcept', 'match', 'assert', 'boolop', 'ternary']
