#!/usr/bin/env python3
"""
问题跟踪系统

用于跟踪和管理反编译器中的问题
"""

import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum

class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 严重：导致崩溃或完全无法使用
    HIGH = "high"            # 高：主要功能受影响
    MEDIUM = "medium"        # 中：次要功能受影响
    LOW = "low"              # 低：轻微问题或优化建议

class IssueStatus(Enum):
    """问题状态"""
    OPEN = "open"                    # 待处理
    IN_PROGRESS = "in_progress"      # 处理中
    FIXED = "fixed"                  # 已修复
    VERIFIED = "verified"            # 已验证
    CLOSED = "closed"                # 已关闭
    WONT_FIX = "wont_fix"            # 不修复
    DUPLICATE = "duplicate"          # 重复

class IssueType(Enum):
    """问题类型"""
    SYNTAX_ERROR = "syntax_error"        # 语法错误
    LOGIC_ERROR = "logic_error"          # 逻辑错误
    PERFORMANCE = "performance"          # 性能问题
    BOUNDARY_CASE = "boundary_case"      # 边界情况
    MISSING_FEATURE = "missing_feature"  # 缺失功能
    DOCUMENTATION = "documentation"      # 文档问题

@dataclass
class Issue:
    """问题数据类"""
    issue_id: str                       # 问题ID
    title: str                          # 标题
    description: str                    # 描述
    pattern: str                        # 相关模式
    issue_type: str                     # 问题类型
    severity: str                       # 严重程度
    status: str                         # 状态
    test_case: Optional[str]            # 关联的测试用例
    root_cause: Optional[str]           # 根本原因
    solution: Optional[str]             # 解决方案
    affected_files: List[str]           # 受影响的文件
    created_at: str                     # 创建时间
    updated_at: str                     # 更新时间
    resolved_at: Optional[str]          # 解决时间
    created_by: str                     # 创建者
    assigned_to: Optional[str]          # 分配给
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Issue':
        return cls(**data)

class IssueTracker:
    """问题跟踪器"""
    
    def __init__(self, issues_file: str = "issues.json"):
        self.issues_file = issues_file
        self.issues: Dict[str, Issue] = {}
        self.load_issues()
    
    def load_issues(self):
        """加载问题"""
        try:
            with open(self.issues_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    issue = Issue.from_dict(item)
                    self.issues[issue.issue_id] = issue
        except FileNotFoundError:
            pass
    
    def save_issues(self):
        """保存问题"""
        data = [issue.to_dict() for issue in self.issues.values()]
        with open(self.issues_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_issue(self, title: str, description: str, pattern: str,
                    issue_type: str, severity: str, test_case: Optional[str] = None,
                    created_by: str = "system") -> str:
        """创建问题"""
        # 生成唯一ID
        content = f"{title}:{pattern}:{datetime.now().isoformat()}"
        issue_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        issue = Issue(
            issue_id=issue_id,
            title=title,
            description=description,
            pattern=pattern,
            issue_type=issue_type,
            severity=severity,
            status=IssueStatus.OPEN.value,
            test_case=test_case,
            root_cause=None,
            solution=None,
            affected_files=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resolved_at=None,
            created_by=created_by,
            assigned_to=None
        )
        
        self.issues[issue_id] = issue
        self.save_issues()
        return issue_id
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """获取问题"""
        return self.issues.get(issue_id)
    
    def update_issue(self, issue_id: str, **kwargs) -> bool:
        """更新问题"""
        if issue_id not in self.issues:
            return False
        
        issue = self.issues[issue_id]
        for key, value in kwargs.items():
            if hasattr(issue, key):
                setattr(issue, key, value)
        
        issue.updated_at = datetime.now().isoformat()
        self.save_issues()
        return True
    
    def fix_issue(self, issue_id: str, solution: str, affected_files: List[str]) -> bool:
        """修复问题"""
        return self.update_issue(
            issue_id,
            status=IssueStatus.FIXED.value,
            solution=solution,
            affected_files=affected_files,
            resolved_at=datetime.now().isoformat()
        )
    
    def verify_issue(self, issue_id: str) -> bool:
        """验证问题已修复"""
        return self.update_issue(
            issue_id,
            status=IssueStatus.VERIFIED.value
        )
    
    def close_issue(self, issue_id: str) -> bool:
        """关闭问题"""
        return self.update_issue(
            issue_id,
            status=IssueStatus.CLOSED.value
        )
    
    def get_issues_by_pattern(self, pattern: str) -> List[Issue]:
        """按模式获取问题"""
        return [i for i in self.issues.values() if i.pattern == pattern]
    
    def get_issues_by_status(self, status: str) -> List[Issue]:
        """按状态获取问题"""
        return [i for i in self.issues.values() if i.status == status]
    
    def get_issues_by_severity(self, severity: str) -> List[Issue]:
        """按严重程度获取问题"""
        return [i for i in self.issues.values() if i.severity == severity]
    
    def get_open_issues(self) -> List[Issue]:
        """获取待处理问题"""
        return self.get_issues_by_status(IssueStatus.OPEN.value)
    
    def generate_report(self) -> Dict:
        """生成问题报告"""
        total = len(self.issues)
        open_issues = len(self.get_open_issues())
        fixed_issues = len(self.get_issues_by_status(IssueStatus.FIXED.value))
        verified_issues = len(self.get_issues_by_status(IssueStatus.VERIFIED.value))
        
        by_pattern = {}
        by_severity = {}
        by_type = {}
        
        for issue in self.issues.values():
            by_pattern[issue.pattern] = by_pattern.get(issue.pattern, 0) + 1
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total,
                'open': open_issues,
                'fixed': fixed_issues,
                'verified': verified_issues,
                'resolution_rate': (fixed_issues + verified_issues) / total * 100 if total > 0 else 0
            },
            'by_pattern': by_pattern,
            'by_severity': by_severity,
            'by_type': by_type,
            'open_issues': [
                {
                    'issue_id': i.issue_id,
                    'title': i.title,
                    'pattern': i.pattern,
                    'severity': i.severity
                }
                for i in self.get_open_issues()
            ]
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="问题跟踪系统")
    parser.add_argument("--create", help="创建问题", action="store_true")
    parser.add_argument("--title", help="问题标题")
    parser.add_argument("--description", help="问题描述")
    parser.add_argument("--pattern", help="相关模式")
    parser.add_argument("--type", help="问题类型", default="syntax_error")
    parser.add_argument("--severity", help="严重程度", default="medium")
    parser.add_argument("--fix", help="修复问题")
    parser.add_argument("--solution", help="解决方案")
    parser.add_argument("--verify", help="验证问题")
    parser.add_argument("--close", help="关闭问题")
    parser.add_argument("--report", help="生成报告", action="store_true")
    parser.add_argument("--list", help="列出问题", choices=['open', 'fixed', 'all'])
    
    args = parser.parse_args()
    
    tracker = IssueTracker()
    
    if args.create:
        if not all([args.title, args.description, args.pattern]):
            print("错误: 创建问题需要提供 --title, --description, --pattern")
            return 1
        
        issue_id = tracker.create_issue(
            args.title, args.description, args.pattern,
            args.type, args.severity
        )
        print(f"已创建问题: {issue_id}")
    
    elif args.fix:
        if tracker.fix_issue(args.fix, args.solution or "", []):
            print(f"已修复问题: {args.fix}")
        else:
            print(f"问题不存在: {args.fix}")
    
    elif args.verify:
        if tracker.verify_issue(args.verify):
            print(f"已验证问题: {args.verify}")
        else:
            print(f"问题不存在: {args.verify}")
    
    elif args.close:
        if tracker.close_issue(args.close):
            print(f"已关闭问题: {args.close}")
        else:
            print(f"问题不存在: {args.close}")
    
    elif args.report:
        report = tracker.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.list:
        if args.list == 'open':
            issues = tracker.get_open_issues()
        elif args.list == 'fixed':
            issues = tracker.get_issues_by_status(IssueStatus.FIXED.value)
        else:
            issues = list(tracker.issues.values())
        
        print(f"\n共 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  [{issue.issue_id}] {issue.title} ({issue.status})")
    
    else:
        print("问题跟踪系统")
        print(f"总问题数: {len(tracker.issues)}")
        print(f"待处理: {len(tracker.get_open_issues())}")
        print(f"已修复: {len(tracker.get_issues_by_status(IssueStatus.FIXED.value))}")

if __name__ == "__main__":
    import sys
    sys.exit(main())
