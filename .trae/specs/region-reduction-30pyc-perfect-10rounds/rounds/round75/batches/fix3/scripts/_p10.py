# -*- coding: utf-8 -*-
import io
p = r'D:\Temp\opencode\r75gate\center\mirr_exp10\core\cfg\region_analyzer.py'
t = io.open(p, encoding='utf-8').read()
old = """                _f_outer_chain = False
                if _f_cond_pred:
                    for _fp in (block.predecessors or []):
                        _fl = _fp.get_last_instruction()
                        if _fl is None or 'IF_' not in _fl.opname:
                            continue
                        for _fs in (_fp.successors or []):
                            if _fs is block:
                                continue
                            _fsl = _fs.get_last_instruction()
                            if _fsl is not None and 'IF_' in _fsl.opname:
                                _f_outer_chain = True
                                break
                        if _f_outer_chain:
                            break"""
assert t.count(old) == 1, t.count(old)
new = """                _f_outer_chain = False
                _f_seen = set()
                _f_stack = list(block.predecessors or [])
                while _f_stack and not _f_outer_chain:
                    _fp = _f_stack.pop()
                    if id(_fp) in _f_seen:
                        continue
                    _f_seen.add(id(_fp))
                    _fl = _fp.get_last_instruction()
                    if _fl is not None and 'IF_' in _fl.opname:
                        for _fs in (_fp.successors or []):
                            if _fs is block:
                                continue
                            _fsl = _fs.get_last_instruction()
                            if _fsl is not None and 'IF_' in _fsl.opname:
                                _f_outer_chain = True
                                break
                    if not _f_outer_chain:
                        _f_stack.extend(_fp.predecessors or [])"""
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('exp10 patched')
