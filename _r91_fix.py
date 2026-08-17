#!/usr/bin/env python3
"""R91 fix: Add degradation check for elif condition in else_blocks"""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        if getattr(region, 'elif_conditions', None):
            _should_degrade_to_normal = False
            for _ec in region.elif_conditions:
                _ec_entry_region = self.region_analyzer.get_entry_region_for_block(_ec)
                if isinstance(_ec_entry_region, (TryExceptRegion, WithRegion, LoopRegion, MatchRegion)):
                    _should_degrade_to_normal = True
                    break
            if _should_degrade_to_normal:"""

new = """        if getattr(region, 'elif_conditions', None):
            _should_degrade_to_normal = False
            for _ec in region.elif_conditions:
                _ec_entry_region = self.region_analyzer.get_entry_region_for_block(_ec)
                if isinstance(_ec_entry_region, (TryExceptRegion, WithRegion, LoopRegion, MatchRegion)):
                    _should_degrade_to_normal = True
                    break
            # R91: elif condition block should not also be in else_blocks.
            # When the region analyzer misclassifies the else branch as an elif
            # condition (e.g., `if x is None: ... else: if y: ...` misidentified
            # as `if x is None: ... elif y: ...`), the elif chain generator puts
            # else-branch code inside the elif body, changing code scope and
            # causing subsequent code to be wrongly nested.
            if not _should_degrade_to_normal and getattr(region, 'else_blocks', None):
                for _ec in region.elif_conditions:
                    if _ec in region.else_blocks:
                        _should_degrade_to_normal = True
                        break
            if _should_degrade_to_normal:"""

count = content.count(old)
print(f'Found {count} occurrences')
if count == 1:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Applied successfully')
elif count == 0:
    print('Not found or already applied')
else:
    print(f'ERROR: {count} occurrences')
