import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.basic_block import BasicBlock
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion

def _load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def _extract_code_objects(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const, prefix + code.co_name + '.'))
    return result

orig_code = _load_pyc_code('site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc')
orig_map = _extract_code_objects(orig_code)

code = orig_map['<module>.PluginRiskCalculation.get_daily_summary']

# Use pycdc to decompile
import pycdc
result = pycdc.decompile_pyc(code)
print(result)
