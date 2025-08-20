"""
内容验证工具模块
用于检测HTML/XML内容中的未闭合标签
"""

import re
from typing import Tuple, Dict, List
from app.utils.logging import log
import app.config.settings as settings


def _remove_ignorable_tag_blocks(content: str, ignorable_tags: List[str] = None) -> str:
    """
    移除指定的可忽略标签对及其内容
    使用栈算法正确处理嵌套情况
    
    Args:
        content: 原始文本内容
        ignorable_tags: 可忽略的标签列表，如果为None则使用配置中的标签
        
    Returns:
        str: 移除可忽略标签块后的内容
    """
    if not content:
        return content
    
    # 如果没有指定标签列表，使用配置中的标签（保持向后兼容）
    if ignorable_tags is None:
        ignorable_tags = getattr(settings, 'IGNORABLE_TAGS', getattr(settings, 'SPECIFIC_TAGS_TO_CHECK', []))
    
    # 处理所有可忽略标签
    for tag_name in ignorable_tags:
        content = _remove_tag_blocks(content, tag_name)
    
    return content


def _remove_think_blocks(content: str) -> str:
    """
    移除 <think></think> 和 <thinking></thinking> 标签对及其内容
    为了向后兼容性保留此函数，实际调用新的可配置函数
    
    Args:
        content: 原始文本内容
        
    Returns:
        str: 移除think块后的内容
    """
    return _remove_ignorable_tag_blocks(content, ['think', 'thinking'])


def _remove_tag_blocks(content: str, tag_name: str) -> str:
    """
    使用栈算法移除指定标签的完整块
    正确处理嵌套情况
    
    Args:
        content: 原始文本内容
        tag_name: 要移除的标签名（如 'think', 'thinking'）
        
    Returns:
        str: 移除指定标签块后的内容
    """
    if not content:
        return content
    
    # 匹配开始和结束标签的正则表达式
    start_pattern = fr'<{tag_name}\b[^>]*>'
    end_pattern = fr'</{tag_name}>'
    
    result_parts = []
    current_pos = 0
    tag_stack = []  # 栈：存储 (标签名, 开始位置)
    
    # 找到所有标签的位置
    all_tags = []
    
    # 找开始标签
    for match in re.finditer(start_pattern, content, flags=re.IGNORECASE):
        all_tags.append((match.start(), match.end(), 'start', tag_name))
    
    # 找结束标签
    for match in re.finditer(end_pattern, content, flags=re.IGNORECASE):
        all_tags.append((match.start(), match.end(), 'end', tag_name))
    
    # 按位置排序
    all_tags.sort(key=lambda x: x[0])
    
    i = 0
    while i < len(all_tags):
        start_pos, end_pos, tag_type, tag = all_tags[i]
        
        if tag_type == 'start':
            # 遇到开始标签
            if not tag_stack:
                # 栈为空，添加到result_parts中的内容是当前位置之前的内容
                result_parts.append(content[current_pos:start_pos])
            
            tag_stack.append((tag, start_pos))
        
        elif tag_type == 'end':
            # 遇到结束标签
            if tag_stack and tag_stack[-1][0] == tag:
                # 找到匹配的开始标签
                start_tag, block_start = tag_stack.pop()
                
                if not tag_stack:
                    # 栈变为空，说明找到了完整的块
                    current_pos = end_pos  # 跳过整个块
        
        i += 1
    
    # 添加剩余的内容
    result_parts.append(content[current_pos:])
    
    return ''.join(result_parts)


def has_unclosed_specific_tags(content: str, tags_to_check: List[str] = None) -> bool:
    """
    检测指定标签列表中的标签是否未闭合
    只检测用户关心的特定标签，忽略其他所有标签
    
    Args:
        content: 要检测的文本内容
        tags_to_check: 需要检测的标签列表，如果为None则使用配置中的标签
        
    Returns:
        bool: True表示指定标签中有未闭合的，False表示指定标签都正确闭合或无相关标签
    """
    if not content or not content.strip():
        return False
    
    # 快速预检：如果内容中没有标签，直接返回
    if '<' not in content or '>' not in content:
        return False
    
    # 如果没有指定标签列表，使用配置中的标签
    if tags_to_check is None:
        tags_to_check = settings.SPECIFIC_TAGS_TO_CHECK
    
    # 如果没有配置要检测的标签，直接返回
    if not tags_to_check:
        return False
    
    try:
        # 移除HTML注释，避免注释中的标签影响检测
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 移除自闭合标签 <tag/> 和 <tag />
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_comments)
        
        # 使用字典记录每种标签的开启次数
        tag_counts = {}
        
        # 将要检测的标签转为小写以便比较
        tags_to_check_lower = [tag.lower() for tag in tags_to_check]
        
        # 匹配任意标签名，支持自定义标签
        # 标签名规则：以字母开头，可包含字母、数字、连字符、下划线
        tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9_-]*)[^>]*>'
        
        for match in re.finditer(tag_pattern, content_no_self_closing):
            is_closing = bool(match.group(1))  # 检查是否是闭合标签 </tag>
            tag_name = match.group(2).lower()  # 标签名，转为小写统一处理
            
            # 只处理需要检测的标签
            if tag_name not in tags_to_check_lower:
                continue
            
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
        
        # 检查是否有任何指定标签未闭合（计数 > 0）
        for tag_name, count in tag_counts.items():
            if count > 0:
                return True  # 发现第一个未闭合的指定标签就返回
        
        return False
        
    except Exception as e:
        # 如果检测过程中出现异常，记录日志但不阻断流程
        log('warning', f"指定标签闭合检测异常: {str(e)}")
        return False  # 异常情况下认为没有问题，避免误判


def has_unclosed_tags(content: str) -> bool:
    """
    检测内容中是否有未闭合标签（保持向后兼容的旧函数）
    
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
        
        # 移除可忽略标签块，忽略其中的标签
        content_no_ignorable = _remove_ignorable_tag_blocks(content_no_comments)
        
        # 移除自闭合标签 <tag/> 和 <tag />
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_ignorable)
        
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


def has_missing_or_unclosed_required_tags(content: str, required_tags: List[str] = None) -> bool:
    """
    检测必须标签是否缺失或未正确闭合
    所有必须标签都必须存在且正确闭合
    
    Args:
        content: 要检测的文本内容
        required_tags: 必须存在的标签列表，如果为None则使用配置中的标签
        
    Returns:
        bool: True表示有缺失或未闭合的必须标签，False表示所有必须标签都存在且正确闭合
    """
    if not content or not content.strip():
        # 如果内容为空，但有必须标签要求，则认为缺失
        if required_tags is None:
            required_tags = settings.REQUIRED_TAGS
        return len(required_tags) > 0
    
    # 如果没有指定必须标签列表，使用配置中的标签
    if required_tags is None:
        required_tags = settings.REQUIRED_TAGS
    
    # 如果没有配置必须标签，直接返回
    if not required_tags:
        return False
    
    # 快速预检：如果内容中没有标签，但要求必须标签，则缺失
    if '<' not in content or '>' not in content:
        return True
    
    try:
        # 移除HTML注释，避免注释中的标签影响检测
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 移除自闭合标签 <tag/> 和 <tag />
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_comments)
        
        # 使用字典记录每种标签的开启次数
        tag_counts = {}
        
        # 将必须标签转为小写以便比较
        required_tags_lower = [tag.lower() for tag in required_tags]
        
        # 初始化所有必须标签的计数为0
        for tag in required_tags_lower:
            tag_counts[tag] = 0
        
        # 匹配任意标签名，支持自定义标签
        # 标签名规则：以字母开头，可包含字母、数字、连字符、下划线
        tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9_-]*)[^>]*>'
        
        for match in re.finditer(tag_pattern, content_no_self_closing):
            is_closing = bool(match.group(1))  # 检查是否是闭合标签 </tag>
            tag_name = match.group(2).lower()  # 标签名，转为小写统一处理
            
            # 只处理必须的标签
            if tag_name not in required_tags_lower:
                continue
            
            if not is_closing:  # 开始标签 <tag>
                tag_counts[tag_name] += 1
            else:  # 结束标签 </tag>
                tag_counts[tag_name] -= 1
                # 如果某个标签的计数变成负数，重置为0
                if tag_counts[tag_name] < 0:
                    tag_counts[tag_name] = 0
        
        # 检查所有必须标签是否都存在且正确闭合
        for tag_name in required_tags_lower:
            count = tag_counts.get(tag_name, 0)
            if count != 0:  # 不等于0说明未正确闭合或未出现
                return True  # 发现未正确闭合的必须标签
        
        # 检查所有必须标签是否都至少出现过一次
        for tag_name in required_tags_lower:
            # 重新扫描检查标签是否至少出现过一次
            start_pattern = fr'<{tag_name}\b[^>]*>'
            if not re.search(start_pattern, content_no_self_closing, flags=re.IGNORECASE):
                return True  # 发现缺失的必须标签
        
        return False
        
    except Exception as e:
        # 如果检测过程中出现异常，记录日志但保守处理
        log('warning', f"必须标签检测异常: {str(e)}")
        return True  # 异常情况下认为有问题，触发重试


def quick_unclosed_check(content: str) -> bool:
    """
    快速检测版本，用于性能敏感场景
    现在使用新的指定标签检测逻辑
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        bool: True表示有未闭合的指定标签，False表示没有问题
    """
    # 预检查：无内容或无标签直接返回
    if not content or '<' not in content:
        return False
    
    return has_unclosed_specific_tags(content)


def quick_required_tags_check(content: str) -> bool:
    """
    快速必须标签检测版本，用于性能敏感场景
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        bool: True表示有缺失或未闭合的必须标签，False表示没有问题
    """
    return has_missing_or_unclosed_required_tags(content)


def debug_unclosed_tags(content: str) -> Tuple[bool, Dict[str, int]]:
    """
    调试版本：返回详细的指定标签统计信息
    用于日志记录和问题排查
    
    Args:
        content: 要检测的文本内容
        
    Returns:
        Tuple[bool, Dict[str, int]]: (是否有未闭合的指定标签, 未闭合指定标签的详细信息)
    """
    if not content or '<' not in content:
        return False, {}
    
    try:
        # 获取要检测的标签列表
        tags_to_check = settings.SPECIFIC_TAGS_TO_CHECK
        if not tags_to_check:
            return False, {}
        
        # 处理内容
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        content_no_self_closing = re.sub(r'<[^>]+/\s*>', '', content_no_comments)
        
        tag_counts = {}
        tags_to_check_lower = [tag.lower() for tag in tags_to_check]
        tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9_-]*)[^>]*>'
        
        for match in re.finditer(tag_pattern, content_no_self_closing):
            is_closing = bool(match.group(1))
            tag_name = match.group(2).lower()
            
            # 只处理需要检测的标签
            if tag_name not in tags_to_check_lower:
                continue
            
            if tag_name not in tag_counts:
                tag_counts[tag_name] = 0
            
            if not is_closing:
                tag_counts[tag_name] += 1
            else:
                tag_counts[tag_name] -= 1
                if tag_counts[tag_name] < 0:
                    tag_counts[tag_name] = 0
        
        # 找出未闭合的指定标签
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
        ("<think>这里有未闭合标签<div></think><span>正常内容</span>", False, "可忽略标签块中的未闭合标签应被忽略"),
        ("<thinking><p>测试内容</thinking><div>未闭合标签", True, "可忽略标签块外的未闭合标签应被检测"),
        ("<think><span>嵌套未闭合</think><div>正常内容</div>", False, "可忽略标签块中嵌套未闭合标签应被忽略"),
        ("正常内容<thinking><div><p>多层嵌套</thinking>其他内容", False, "可忽略标签块中多层嵌套应被忽略"),
        ("<THINK>大写标签<div>测试</THINK><span>内容</span>", False, "大写可忽略标签应被正确处理"),
        ("<assess>评估内容<div>未闭合</assess><span>正常</span>", False, "assess标签块中的未闭合标签应被忽略"),
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