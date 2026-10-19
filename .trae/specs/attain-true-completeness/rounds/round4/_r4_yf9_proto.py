#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 YF9 prototype: Yield/YieldFrom operand precedence (parenthesize in BinOp etc.)."""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg.code_generator import CodeGenerator
from core.ast_nodes import ASTYield

_orig_expr = CodeGenerator._generate_expression
_orig_dict_prec = CodeGenerator._get_dict_expr_precedence
_orig_ast_prec = CodeGenerator._get_ast_expr_precedence


def _wrap(self, node, parent_precedence):
    if isinstance(node, dict) and node.get('type') in ('Yield', 'YieldFrom') and parent_precedence > 0:
        inner = _orig_expr(self, node, 0)
        if not (inner.startswith('(') and inner.endswith(')')):
            return f'({inner})'
        return inner
    if isinstance(node, ASTYield) and parent_precedence > 0:
        inner = _orig_expr(self, node, 0)
        if not (inner.startswith('(') and inner.endswith(')')):
            return f'({inner})'
        return inner
    return _orig_expr(self, node, parent_precedence)


def _dict_prec(self, node):
    if isinstance(node, dict) and node.get('type') in ('Yield', 'YieldFrom'):
        return self._precedence['lambda']
    return _orig_dict_prec(self, node)


def _ast_prec(self, node):
    if isinstance(node, ASTYield):
        return self._precedence['lambda']
    return _orig_ast_prec(self, node)


CodeGenerator._generate_expression = _wrap
CodeGenerator._get_dict_expr_precedence = _dict_prec
CodeGenerator._get_ast_expr_precedence = _ast_prec

import pycdc

pyc = sys.argv[1]
src = pycdc.decompile_pyc(pyc)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('written', sys.argv[2])
