import sys
sys.path.insert(0, '.')
import core.cfg.region_analyzer as ra

orig_identify = ra.RegionAnalyzer._identify_conditional_regions

def patched_identify(self, *args, **kwargs):
    result = orig_identify(self, *args, **kwargs)
    # Check which regions contain block 72
    for r in self.regions:
        if hasattr(r, 'entry') and r.entry and r.entry.start_offset == 72:
            print(f"[REGION] Block 72 is entry of: {type(r).__name__} region_type={getattr(r, 'region_type', None)}")
        if hasattr(r, 'blocks') and any(b.start_offset == 72 for b in r.blocks):
            print(f"[REGION] Block 72 is in: {type(r).__name__} region_type={getattr(r, 'region_type', None)} entry={r.entry.start_offset}")
    return result

ra.RegionAnalyzer._identify_conditional_regions = patched_identify

from pycdc import decompile_pyc
result = decompile_pyc(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_fly_data\fly_api\history_api.pyc')
print("\nDone")
