"""
内容验证工具模块
用于检测HTML/XML内容中的未闭合标签
"""

import re
from typing import Tuple, Dict
from app.utils.logging import log


def has_unclosed_tags(content: str) -> bool:
    """
    检测内容中是否有未闭合标签
    
    专门针对以下场景优化：
    - 绝大多数情况是开始标签没有对应的闭合标签
    - 几乎不会出现孤立的闭合标签
    - 支持自定义标签和标准HTML标签
    - 自动跳过无标签的纯文本内容
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        bool: True表示有未闭合标签，False表示标签正确闭合或无标签
    """
    if not content or not content.strip():
        return False
    
    # 快速预检：如果内容中没有标签，直接返回
    if '<' not in content or '>' not in content:
        return False
    
    try:
        # 移除HTML注释，避免注释中的标签影响检测
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 移除自闭合标签 <tag/> 和 <tag />
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_comments)
        
        # 使用字典记录每种标签的开启次数
        tag_counts = {}
        
        # 匹配任意标签名，支持自定义标签
        # 标签名规则：以字母开头，可包含字母、数字、连字符、下划线
        tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9_-]*)[^>]*>'
        
        for match in re.finditer(tag_pattern, content_no_self_closing):
            is_closing = bool(match.group(1))  # 检查是否是闭合标签 </tag>
            tag_name = match.group(2).lower()  # 标签名，转为小写统一处理
            
            # 初始化标签计数器
            if tag_name not in tag_counts:
                tag_counts[tag_name] = 0
            
            if not is_closing:  # 开始标签 <tag>
                tag_counts[tag_name] += 1
            else:  # 结束标签 </tag>
                tag_counts[tag_name] -= 1
                # 如果某个标签的计数变成负数，重置为0
                # 因为根据实际情况，几乎不会出现"只有闭合标签"的情况
                if tag_counts[tag_name] < 0:
                    tag_counts[tag_name] = 0
        
        # 检查是否有任何标签未闭合（计数 > 0）
        for tag_name, count in tag_counts.items():
            if count > 0:
                return True  # 发现第一个未闭合标签就返回
        
        return False
        
    except Exception as e:
        # 如果检测过程中出现异常，记录日志但不阻断流程
        log('warning', f"未闭合标签检测异常: {str(e)}")
        return False  # 异常情况下认为没有问题，避免误判


def quick_unclosed_check(content: str) -> bool:
    """
    快速检测版本，用于性能敏感场景
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        bool: True表示有未闭合标签，False表示没有问题
    """
    # 预检查：无内容或无标签直接返回
    if not content or '<' not in content:
        return False
    
    return has_unclosed_tags(content)


def debug_unclosed_tags(content: str) -> Tuple[bool, Dict[str, int]]:
    """
    调试版本：返回详细的标签统计信息
    用于日志记录和问题排查
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        Tuple[bool, Dict[str, int]]: (是否有未闭合标签, 未闭合标签的详细信息)
    """
    if not content or '<' not in content:
        return False, {}
    
    try:
        # 处理内容
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_comments)
        
        tag_counts = {}
        tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9_-]*)[^>]*>'
        
        for match in re.finditer(tag_pattern, content_no_self_closing):
            is_closing = bool(match.group(1))
            tag_name = match.group(2).lower()
            
            if tag_name not in tag_counts:
                tag_counts[tag_name] = 0
            
            if not is_closing:
                tag_counts[tag_name] += 1
            else:
                tag_counts[tag_name] -= 1
                if tag_counts[tag_name] < 0:
                    tag_counts[tag_name] = 0
        
        # 找出未闭合的标签
        unclosed_tags = {tag: count for tag, count in tag_counts.items() if count > 0}
        has_unclosed = len(unclosed_tags) > 0
        
        return has_unclosed, unclosed_tags
        
    except Exception as e:
        log('warning', f"调试检测异常: {str(e)}")
        return False, {}


# 模块测试函数（可选）
def _test_validator():
    """
    简单的测试函数，用于验证检测器的基本功能
    """
    test_cases = [
        ("", False, "空内容"),
        ("纯文本内容", False, "无标签文本"),
        ("<div>完整标签</div>", False, "正确闭合的标签"), 
        ("<div>未闭合标签", True, "未闭合的div标签"),
        ("<img src='test.jpg'/>", False, "自闭合标签"),
        ("<!-- <div>注释中的标签</div> --> <span>正常内容</span>", False, "含注释的正确内容"),
        ("<custom-tag>自定义标签</custom-tag>", False, "自定义标签正确闭合"),
        ("<my-component>自定义未闭合", True, "自定义标签未闭合"),
    ]
    
    print("开始测试内容验证器...")
    for content, expected, description in test_cases:
        result = has_unclosed_tags(content)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: {result}")
    
    # 调试信息测试
    debug_content = "<div><span>测试</span><p>未闭合"
    has_unclosed, details = debug_unclosed_tags(debug_content)
    print(f"\n调试信息测试: {has_unclosed}, 详情: {details}")


if __name__ == "__main__":
    _test_validator()