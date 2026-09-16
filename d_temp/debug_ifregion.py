import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pyc_loader_v2 import load_pyc_file_v2
from core.control_flow import ControlFlowAnalyzer
from bytecode.pyc_disasm import PycDisassembler

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
pyc_data = load_pyc_file_v2(pyc_path)
disasm = PycDisassembler()
functions = disasm.disassemble(pyc_data)

for func_name, func_info in functions.items():
    if func_name == 'handle_exrights':
        analyzer = ControlFlowAnalyzer(func_info, func_name)
        analyzer.analyze()
        for r in analyzer.region_analyzer.regions:
            if hasattr(r, 'condition_block') and r.condition_block and r.condition_block.start_offset == 6:
                print('IfRegion: cond_block=%d' % r.condition_block.start_offset)
                print('  then_blocks=%s' % [b.start_offset for b in r.then_blocks])
                print('  else_blocks=%s' % [b.start_offset for b in r.else_blocks])
                ibc = getattr(r, 'inline_boolop_chains', {})
                for k, v in ibc.items():
                    print('  inline_boolop_chains[%d]: blocks=%s, op=%s' % (k, [b.start_offset for b in v['blocks']], v['op']))
                print('  entry=%s' % (r.entry.start_offset if r.entry else None))
                if hasattr(r, 'merge_block') and r.merge_block:
                    print('  merge_block=%d' % r.merge_block.start_offset)
