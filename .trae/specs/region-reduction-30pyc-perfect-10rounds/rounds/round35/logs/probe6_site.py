# -*- coding: utf-8 -*-
"""R35 read-only probe #6: which call site emits the disputed `return None` (block @1970)?

Wraps RegionASTGenerator._generate_handler_body_statements, records every call that returns a
`Return`-of-None statement together with the emitting caller line, then decompiles the target
into scratch (the tracked product is never touched).
"""
import importlib.util
import io
import os
import sys
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg import region_ast_generator as RAG  # noqa: E402

LOG = []
_orig = RAG.RegionASTGenerator._generate_handler_body_statements


def _is_return_none(stmts):
    if len(stmts) != 1:
        return False
    s = stmts[0]
    return s.get('type') == 'Return' and (s.get('value') or {}).get('type') == 'Constant' \
        and (s.get('value') or {}).get('value') is None


def wrapped(self, block):
    r = _orig(self, block)
    if _is_return_none(r):
        site = None
        for fr in reversed(traceback.extract_stack()[:-1]):
            if fr.filename.endswith('region_ast_generator.py') and fr.lineno != 25627:
                site = (fr.lineno, fr.line)
                break
        LOG.append('block@%-6s ops=%-46s role=%-16s caller=%s' % (
            block.start_offset,
            ' '.join(i.opname for i in block.instructions if i.opname != 'CACHE')[:46],
            str(self.region_analyzer.get_block_role(block)), site))
    return r


RAG.RegionASTGenerator._generate_handler_body_statements = wrapped

_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

PYC = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
dst = os.path.join(OUT, 'r35_target_product.py')
if os.path.isfile(dst):
    os.remove(dst)
res = pbv.decompile_single(PYC, dst)
prod = io.open(dst, encoding='utf-8-sig').read().replace('\r\n', '\n')
tracked = io.open(REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/functionOK.py',
                  encoding='utf-8-sig').read().replace('\r\n', '\n')
head = ['decompile_single -> %r' % (list(res.keys())[:6] if isinstance(res, dict) else res),
        'fresh product == tracked product: %s' % (prod == tracked)]
head.append('emitted Return(None) statements from _generate_handler_body_statements:')
io.open(os.path.join(OUT, 'probe6_site.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(head + LOG) + '\n')
print('\n'.join(head + LOG))
