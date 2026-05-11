"""方法合规性审计工具 (Task 29)"""
import ast, re, os
from typing import Dict, List, Tuple, Any, Optional

class MethodAuditor:
    """方法合规性审计工具"""

    def __init__(self, source_files: List[str]):
        self.source_files = source_files
        self.results: Dict[str, Any] = {}

    region_analyzer_allowed_methods = {
        '__init__', 'analyze', 'build_regions', 'get_region_type',
        'get_successors', 'get_predecessors', 'is_entry', 'is_exit',
        'is_loop_header', 'is_merge_point', 'contains_try',
        'region_for_block', 'dominator_tree', 'post_dominator_tree',
        'immediate_dominator', 'immediate_post_dominator',
        'dominance_frontier', 'iterate_dominance',
        'find_natural_loops', 'find_back_edges', 'find_loop_body',
        'classify_region', 'reduce_structured', 'structure_tree',
        'interval_analysis', 'node_info', 'edge_info',
        '_visit_node', '_collect_nodes', '_reset_state',
    }
    region_analyzer_max_methods = 32

    region_ast_generator_allowed_methods = {
        '__init__', 'generate', 'visit_region', 'visit_basic',
        'visit_if_region', 'visit_while_loop', 'visit_for_loop',
        'visit_try_except', 'visit_with_region', 'visit_match_region',
        'visit_bool_op', 'visit_ternary', 'emit_assign',
        'emit_expr', 'emit_return', 'emit_pass', 'emit_break',
        'emit_continue', 'emit_raise', 'emit_delete', 'emit_global',
        'emit_nonlocal', 'emit_import', 'emit_assert', 'emit_yield',
        'new_label', 'current_label', 'push_scope', 'pop_scope',
    }
    region_ast_generator_max_methods = 25

    forbidden_patterns = [
        (r'_fix_', 'fix_pattern'),
        (r'_merge_condition', 'merge_condition_pattern'),
        (r'_patch_', 'patch_pattern'),
        (r'_hack_', 'hack_pattern'),
        (r'_workaround_', 'workaround_pattern'),
        (r'_quick_fix', 'quick_fix_pattern'),
        (r'__internal__', 'internal_double_underscore'),
    ]
    forbidden_suffix_patterns = [r'_from_block$', r'_from_node$', r'_raw$', r'_unsafe$', r'_bypass$']

    def _parse_file(self, filepath: str) -> Optional[ast.AST]:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            return ast.parse(source, filename=filepath)
        except SyntaxError:
            return None

    def _extract_methods(self, tree: ast.AST) -> List[Tuple[str, ast.FunctionDef]]:
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append((item.name, item))
        return methods

    def audit_region_analyzer(self) -> Dict[str, Any]:
        result = {'file': self.source_files[0] if len(self.source_files) > 0 else '', 'status': 'PASS', 'issues': [], 'method_count': 0, 'methods_found': [], 'violations': []}
        filepath = result['file']
        if not filepath:
            result['status'] = 'SKIP'; result['issues'].append('unspecified path'); return result
        tree = self._parse_file(filepath)
        if tree is None:
            result['status'] = 'ERROR'; result['issues'].append('cannot parse: ' + filepath); return result
        methods = self._extract_methods(tree)
        method_names = [m[0] for m in methods]
        result['method_count'] = len(methods)
        result['methods_found'] = sorted(method_names)
        if len(methods) > self.region_analyzer_max_methods:
            result['status'] = 'FAIL'
            msg = 'methods exceed limit: %d > %d' % (len(methods), self.region_analyzer_max_methods)
            result['violations'].append(msg); result['issues'].append(msg)
        unknown = set(method_names) - self.region_analyzer_allowed_methods
        if unknown:
            result['status'] = 'FAIL'
            msg = 'unknown methods: ' + str(sorted(unknown))
            result['violations'].append(msg); result['issues'].append(msg)
        return result

    def audit_ast_generator(self) -> Dict[str, Any]:
        result = {'file': self.source_files[1] if len(self.source_files) > 1 else '', 'status': 'PASS', 'issues': [], 'method_count': 0, 'methods_found': [], 'violations': []}
        filepath = result['file']
        if not filepath:
            result['status'] = 'SKIP'; result['issues'].append('unspecified path'); return result
        tree = self._parse_file(filepath)
        if tree is None:
            result['status'] = 'ERROR'; result['issues'].append('cannot parse: ' + filepath); return result
        methods = self._extract_methods(tree)
        method_names = [m[0] for m in methods]
        result['method_count'] = len(methods)
        result['methods_found'] = sorted(method_names)
        if len(methods) > self.region_ast_generator_max_methods:
            result['status'] = 'FAIL'
            msg = 'methods exceed limit: %d > %d' % (len(methods), self.region_ast_generator_max_methods)
            result['violations'].append(msg); result['issues'].append(msg)
        unknown = set(method_names) - self.region_ast_generator_allowed_methods
        if unknown:
            result['status'] = 'FAIL'
            msg = 'unknown methods: ' + str(sorted(unknown))
            result['violations'].append(msg); result['issues'].append(msg)
        suffix_violations = []
        for name in method_names:
            for pat in self.forbidden_suffix_patterns:
                if re.search(pat, name):
                    suffix_violations.append(name); break
        if suffix_violations:
            result['status'] = 'FAIL'
            msg = 'forbidden suffix: ' + str(suffix_violations)
            result['violations'].append(msg); result['issues'].append(msg)
        return result

    def audit_forbidden_patterns(self) -> Dict[str, Any]:
        result = {'status': 'PASS', 'issues': [], 'violations_by_file': {}}
        for filepath in self.source_files:
            tree = self._parse_file(filepath)
            if tree is None: continue
            methods = self._extract_methods(tree)
            file_violations = []
            for name, node in methods:
                for pattern, label in self.forbidden_patterns:
                    if re.search(pattern, name):
                        file_violations.append({'method': name, 'pattern': label, 'regex': pattern, 'line': getattr(node, 'lineno', 0)})
            if file_violations:
                result['status'] = 'FAIL'; result['issues'].append(filepath + ': ' + str(len(file_violations)) + ' violations')
            result['violations_by_file'][filepath] = file_violations
        return result

    def audit_cross_domain_access(self) -> Dict[str, Any]:
        result = {'status': 'PASS', 'issues': [], 'cross_accesses': []}
        cross_patterns = [
            (r'region_analyzer\.RegionAnalyzer', 'ASTGen accesses RegionAnalyzer'),
            (r'cfg_builder\.CFGBuilder', 'non-CFG module accesses CFGBuilder'),
            (r'code_generator\.CodeGenerator', 'low-level module accesses CodeGenerator'),
        ]
        for filepath in self.source_files:
            if not os.path.exists(filepath): continue
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            for pattern, desc in cross_patterns:
                matches = re.findall(pattern, source)
                if matches:
                    result['cross_accesses'].append({'file': filepath, 'type': desc, 'count': len(matches), 'pattern': pattern})
        if result['cross_accesses']:
            result['status'] = 'WARNING'
            for ca in result['cross_accesses']:
                result['issues'].append(ca['file'] + ': ' + ca['type'] + ' (' + str(ca['count']) + ')')
        return result

    def run_full_audit(self) -> Dict[str, Any]:
        self.results = {
            'region_analyzer': self.audit_region_analyzer(),
            'ast_generator': self.audit_ast_generator(),
            'forbidden_patterns': self.audit_forbidden_patterns(),
            'cross_domain': self.audit_cross_domain_access(),
        }
        overall = 'PASS'
        for key, val in self.results.items():
            if val.get('status') == 'FAIL':
                overall = 'FAIL'; break
            elif val.get('status') == 'ERROR' and overall != 'FAIL':
                overall = 'ERROR'
            elif val.get('status') == 'WARNING' and overall == 'PASS':
                overall = 'WARNING'
        self.results['overall_status'] = overall
        return self.results

    def generate_report(self) -> str:
        if not self.results: self.run_full_audit()
        lines = []
        lines.append('=' * 60)
        lines.append('  Task 29 Method Compliance Audit Report')
        lines.append('=' * 60); lines.append('')
        ra = self.results.get('region_analyzer', {})
        lines.append('[1] RegionAnalyzer Audit')
        lines.append('    file: ' + str(ra.get('file', 'N/A')))
        lines.append('    status: ' + str(ra.get('status', 'N/A')))
        lines.append('    method count: ' + str(ra.get('method_count', 0)) + ' / ' + str(self.region_analyzer_max_methods))
        if ra.get('methods_found'): lines.append('    methods: ' + ', '.join(ra['methods_found']))
        for issue in ra.get('issues', []): lines.append('    ! ' + issue)
        lines.append('')
        ag = self.results.get('ast_generator', {})
        lines.append('[2] RegionASTGenerator Audit')
        lines.append('    file: ' + str(ag.get('file', 'N/A')))
        lines.append('    status: ' + str(ag.get('status', 'N/A')))
        lines.append('    method count: ' + str(ag.get('method_count', 0)) + ' / ' + str(self.region_ast_generator_max_methods))
        if ag.get('methods_found'): lines.append('    methods: ' + ', '.join(ag['methods_found']))
        for issue in ag.get('issues', []): lines.append('    ! ' + issue)
        lines.append('')
        fp = self.results.get('forbidden_patterns', {})
        lines.append('[3] Forbidden Pattern Detection')
        lines.append('    status: ' + str(fp.get('status', 'N/A')))
        total_violations = sum(len(v) for v in fp.get('violations_by_file', {}).values())
        lines.append('    total violations: ' + str(total_violations))
        for filepath, violations in fp.get('violations_by_file', {}).items():
            if violations:
                lines.append('    --- ' + os.path.basename(filepath) + ' ---')
                for v in violations: lines.append('      @' + str(v['line']) + ' ' + v['method'] + ' [' + v['pattern'] + ']')
        lines.append('')
        cd = self.results.get('cross_domain', {})
        lines.append('[4] Cross-Domain Access Audit')
        lines.append('    status: ' + str(cd.get('status', 'N/A')))
        for ca in cd.get('cross_accesses', []):
            lines.append('    ~ ' + os.path.basename(ca['file']) + ': ' + ca['type'] + ' (' + str(ca['count']) + ')')
        lines.append('')
        lines.append('=' * 60)
        overall = self.results.get('overall_status', 'UNKNOWN')
        icon_map = {'PASS': '[OK]', 'FAIL': '[FAIL]', 'WARNING': '[WARN]', 'ERROR': '[ERR]', 'SKIP': '[SKIP]'}
        icon = icon_map.get(overall, '[?]')
        lines.append('  Overall: ' + icon + ' ' + overall)
        lines.append('=' * 60)
        return '\n'.join(lines)

if __name__ == '__main__':
    auditor = MethodAuditor([
        'core/cfg/region_analyzer.py',
        'core/cfg/region_ast_generator.py',
    ])
    print(auditor.generate_report())
