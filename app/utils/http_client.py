"""
HTTP客户端工具模块
提供配置了代理的httpx.AsyncClient实例
"""

import httpx
from typing import Optional, Dict, Any
import app.config.settings as settings
from app.utils.logging import log


def get_proxy_config() -> Optional[str]:
    """
    获取代理配置
    
    Returns:
        代理URL字符串，如果没有配置代理则返回None
    """
    # 优先级: SOCKS_PROXY > HTTPS_PROXY > HTTP_PROXY > ALL_PROXY
    if settings.SOCKS_PROXY:
        return settings.SOCKS_PROXY
    elif settings.HTTPS_PROXY:
        return settings.HTTPS_PROXY
    elif settings.HTTP_PROXY:
        return settings.HTTP_PROXY
    elif settings.ALL_PROXY:
        return settings.ALL_PROXY
    
    return None


def create_http_client(timeout: Optional[float] = None, **kwargs) -> httpx.AsyncClient:
    """
    创建配置了代理的httpx.AsyncClient实例
    
    Args:
        timeout: 请求超时时间（秒）
        **kwargs: 传递给httpx.AsyncClient的其他参数
    
    Returns:
        配置了代理的httpx.AsyncClient实例
    """
    # 获取代理配置
    proxy_url = get_proxy_config()
    
    # 设置默认超时
    if timeout is None:
        timeout = 600  # 默认10分钟超时
    
    # 构建客户端参数
    client_kwargs = {
        "timeout": timeout,
        **kwargs
    }
    
    # 如果有代理配置，添加到客户端参数中
    if proxy_url:
        client_kwargs["proxy"] = proxy_url
        
        # 记录使用的代理信息（隐藏认证信息）
        if "@" in proxy_url:
            # 格式: protocol://user:pass@host:port
            parts = proxy_url.split("@")
            if len(parts) >= 2:
                protocol_part = parts[0].split("://")[0] if "://" in parts[0] else "unknown"
                host_part = "@".join(parts[1:])
                safe_proxy = f"{protocol_part}://***:***@{host_part}"
            else:
                safe_proxy = proxy_url
        else:
            safe_proxy = proxy_url
        
        log('info', f"使用代理配置: {safe_proxy}")
    
    return httpx.AsyncClient(**client_kwargs)


def log_proxy_status():
    """
    记录当前代理配置状态
    """
    proxy_url = get_proxy_config()
    if proxy_url:
        # 隐藏认证信息后记录
        if "@" in proxy_url and "://" in proxy_url:
            scheme_auth, host_port = proxy_url.split("@", 1)
            scheme = scheme_auth.split("://")[0]
            safe_proxy = f"{scheme}://***:***@{host_port}"
        else:
            safe_proxy = proxy_url
        log('info', f"代理配置已启用: {safe_proxy}")
    else:
        log('info', "未配置代理，使用直连")