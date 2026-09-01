import sys, os
sys.path.insert(0, '.')

import core.cfg.region_ast_generator as rag

_orig_lge = rag.RegionASTGenerator._loop_generate_for
def lge(self, region):
    fis = region.metadata.get('for_iter_setup')
    if fis is not None:
        terns = []
        for tr in self.region_analyzer.regions:
            if isinstance(tr, rag.TernaryRegion) and tr.merge_block is not None \
               and tr.merge_block.start_offset == fis.start_offset:
                terns.append((tr.merge_context, id(tr) in self._generated_regions,
                              fis in self.generated_blocks,
                              fis.start_offset,
                              sorted(getattr(tr, 'blocks', []) and [b.start_offset for b in tr.blocks])))
        if terns or True:
            print(f"[FOR] setup_off={fis.start_offset} in_generated={fis in self.generated_blocks} entry_prefix={fis in self._entry_prefix_emitted_blocks} self_setup={fis in region.blocks or fis is region.metadata.get('for_iter_setup')}")
            print(f"      matching_ternaries(merge==setup): {terns}")
            # also list all ternaries whose blocks contain this offset
            others = []
            for tr in self.region_analyzer.regions:
                if isinstance(tr, rag.TernaryRegion):
                    offs = [b.start_offset for b in getattr(tr, 'blocks', [])]
                    if any(o <= fis.start_offset < o + 400 for o in offs):
                        others.append((tr.condition_block.start_offset if tr.condition_block else '?',
                                       tr.merge_block.start_offset if tr.merge_block else None,
                                       getattr(tr, 'merge_context', None),
                                       id(tr) in self._generated_regions))
            print(f"      nearby_ternaries: {others}")
    return _orig_lge(self, region)
rag.RegionASTGenerator._loop_generate_for = lge

import pycdc
out = pycdc.decompile_pyc("site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc")
idx = out.find('def get_stock_info')
print(out[idx:idx+1200])
