#!/usr/bin/env python3
"""
度量指标收集器

用于收集和分析模式识别系统的各种度量指标
"""

import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class PatternMetrics:
    """模式度量数据"""
    pattern_name: str
    total_recognitions: int
    successful_recognitions: int
    failed_recognitions: int
    avg_recognition_time_ms: float
    min_recognition_time_ms: float
    max_recognition_time_ms: float
    last_updated: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def success_rate(self) -> float:
        if self.total_recognitions == 0:
            return 0.0
        return self.successful_recognitions / self.total_recognitions * 100

@dataclass
class TestMetrics:
    """测试度量数据"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration_ms: float
    avg_duration_ms: float
    pass_rate: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class FixMetrics:
    """修复度量数据"""
    timestamp: str
    total_issues: int
    open_issues: int
    fixed_issues: int
    verified_issues: int
    avg_fix_time_days: float
    resolution_rate: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

class MetricsCollector:
    """度量指标收集器"""
    
    def __init__(self, metrics_dir: str = "patterns/metrics/data"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.pattern_metrics: Dict[str, PatternMetrics] = {}
        self.test_history: List[TestMetrics] = []
        self.fix_history: List[FixMetrics] = []
        
        self.load_metrics()
    
    def load_metrics(self):
        """加载度量数据"""
        # 加载模式度量
        pattern_file = self.metrics_dir / "pattern_metrics.json"
        if pattern_file.exists():
            with open(pattern_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    pm = PatternMetrics(**item)
                    self.pattern_metrics[pm.pattern_name] = pm
        
        # 加载测试历史
        test_file = self.metrics_dir / "test_history.json"
        if test_file.exists():
            with open(test_file, 'r') as f:
                data = json.load(f)
                self.test_history = [TestMetrics(**item) for item in data]
        
        # 加载修复历史
        fix_file = self.metrics_dir / "fix_history.json"
        if fix_file.exists():
            with open(fix_file, 'r') as f:
                data = json.load(f)
                self.fix_history = [FixMetrics(**item) for item in data]
    
    def save_metrics(self):
        """保存度量数据"""
        # 保存模式度量
        pattern_file = self.metrics_dir / "pattern_metrics.json"
        with open(pattern_file, 'w') as f:
            json.dump([pm.to_dict() for pm in self.pattern_metrics.values()], 
                     f, indent=2)
        
        # 保存测试历史
        test_file = self.metrics_dir / "test_history.json"
        with open(test_file, 'w') as f:
            json.dump([tm.to_dict() for tm in self.test_history], 
                     f, indent=2)
        
        # 保存修复历史
        fix_file = self.metrics_dir / "fix_history.json"
        with open(fix_file, 'w') as f:
            json.dump([fm.to_dict() for fm in self.fix_history], 
                     f, indent=2)
    
    def record_pattern_recognition(self, pattern_name: str, 
                                   success: bool, duration_ms: float):
        """记录模式识别"""
        if pattern_name not in self.pattern_metrics:
            self.pattern_metrics[pattern_name] = PatternMetrics(
                pattern_name=pattern_name,
                total_recognitions=0,
                successful_recognitions=0,
                failed_recognitions=0,
                avg_recognition_time_ms=0.0,
                min_recognition_time_ms=float('inf'),
                max_recognition_time_ms=0.0,
                last_updated=datetime.now().isoformat()
            )
        
        pm = self.pattern_metrics[pattern_name]
        pm.total_recognitions += 1
        
        if success:
            pm.successful_recognitions += 1
        else:
            pm.failed_recognitions += 1
        
        # 更新平均时间
        pm.avg_recognition_time_ms = (
            (pm.avg_recognition_time_ms * (pm.total_recognitions - 1) + duration_ms)
            / pm.total_recognitions
        )
        
        # 更新最小/最大时间
        pm.min_recognition_time_ms = min(pm.min_recognition_time_ms, duration_ms)
        pm.max_recognition_time_ms = max(pm.max_recognition_time_ms, duration_ms)
        
        pm.last_updated = datetime.now().isoformat()
        self.save_metrics()
    
    def record_test_run(self, total: int, passed: int, failed: int, 
                       skipped: int, duration_ms: float):
        """记录测试运行"""
        tm = TestMetrics(
            timestamp=datetime.now().isoformat(),
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            total_duration_ms=duration_ms,
            avg_duration_ms=duration_ms / total if total > 0 else 0,
            pass_rate=passed / total * 100 if total > 0 else 0
        )
        
        self.test_history.append(tm)
        self.save_metrics()
    
    def record_fix_metrics(self, total: int, open_count: int, fixed: int,
                          verified: int, avg_fix_time: float):
        """记录修复度量"""
        fm = FixMetrics(
            timestamp=datetime.now().isoformat(),
            total_issues=total,
            open_issues=open_count,
            fixed_issues=fixed,
            verified_issues=verified,
            avg_fix_time_days=avg_fix_time,
            resolution_rate=(fixed + verified) / total * 100 if total > 0 else 0
        )
        
        self.fix_history.append(fm)
        self.save_metrics()
    
    def get_pattern_performance_report(self) -> Dict:
        """获取模式性能报告"""
        if not self.pattern_metrics:
            return {}
        
        patterns = list(self.pattern_metrics.values())
        
        # 按成功率排序
        by_success_rate = sorted(patterns, key=lambda p: p.success_rate, reverse=True)
        
        # 按平均时间排序
        by_avg_time = sorted(patterns, key=lambda p: p.avg_recognition_time_ms)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_patterns': len(patterns),
                'avg_success_rate': sum(p.success_rate for p in patterns) / len(patterns),
                'avg_recognition_time_ms': sum(p.avg_recognition_time_ms for p in patterns) / len(patterns)
            },
            'top_performers': [
                {'name': p.pattern_name, 'success_rate': p.success_rate}
                for p in by_success_rate[:5]
            ],
            'slowest_patterns': [
                {'name': p.pattern_name, 'avg_time_ms': p.avg_recognition_time_ms}
                for p in by_avg_time[-5:]
            ],
            'problematic_patterns': [
                {'name': p.pattern_name, 'success_rate': p.success_rate}
                for p in patterns if p.success_rate < 90
            ]
        }
    
    def get_test_trend_report(self, days: int = 30) -> Dict:
        """获取测试趋势报告"""
        recent_tests = self.test_history[-days:] if len(self.test_history) > days else self.test_history
        
        if not recent_tests:
            return {}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'period_days': days,
            'summary': {
                'total_runs': len(recent_tests),
                'avg_pass_rate': sum(t.pass_rate for t in recent_tests) / len(recent_tests),
                'avg_duration_ms': sum(t.total_duration_ms for t in recent_tests) / len(recent_tests),
                'trend': 'improving' if recent_tests[-1].pass_rate > recent_tests[0].pass_rate else 'stable'
            },
            'daily_data': [
                {
                    'date': t.timestamp,
                    'pass_rate': t.pass_rate,
                    'duration_ms': t.total_duration_ms
                }
                for t in recent_tests
            ]
        }
    
    def get_comprehensive_report(self) -> Dict:
        """获取综合报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'pattern_performance': self.get_pattern_performance_report(),
            'test_trend': self.get_test_trend_report(),
            'latest_fix_metrics': self.fix_history[-1].to_dict() if self.fix_history else None
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="度量指标收集器")
    parser.add_argument("--report", help="生成报告", choices=['pattern', 'test', 'comprehensive'])
    parser.add_argument("--days", help="天数", type=int, default=30)
    
    args = parser.parse_args()
    
    collector = MetricsCollector()
    
    if args.report == 'pattern':
        report = collector.get_pattern_performance_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.report == 'test':
        report = collector.get_test_trend_report(args.days)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.report == 'comprehensive':
        report = collector.get_comprehensive_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    else:
        print("度量指标收集器")
        print(f"模式数量: {len(collector.pattern_metrics)}")
        print(f"测试历史: {len(collector.test_history)} 条")
        print(f"修复历史: {len(collector.fix_history)} 条")

if __name__ == "__main__":
    import sys
    sys.exit(main())
