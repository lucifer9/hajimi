"""
HTTP客户端工具模块
提供配置了代理的httpx.AsyncClient实例
"""

import httpx
from typing import Optional, Dict, Any
import app.config.settings as settings
from app.utils.logging import log


def get_proxy_config() -> Optional[Dict[str, str]]:
    """
    获取代理配置
    
    Returns:
        代理配置字典，如果没有配置代理则返回None
    """
    proxies = {}
    
    # 优先使用特定协议的代理配置
    if settings.HTTP_PROXY:
        proxies["http://"] = settings.HTTP_PROXY
    if settings.HTTPS_PROXY:
        proxies["https://"] = settings.HTTPS_PROXY
    
    # 如果设置了SOCKS代理，则对所有协议使用SOCKS代理
    if settings.SOCKS_PROXY:
        proxies["http://"] = settings.SOCKS_PROXY
        proxies["https://"] = settings.SOCKS_PROXY
    
    # 如果设置了ALL_PROXY，则作为所有协议的回退代理
    if settings.ALL_PROXY and not proxies:
        proxies["http://"] = settings.ALL_PROXY
        proxies["https://"] = settings.ALL_PROXY
    
    return proxies if proxies else None


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
    proxies = get_proxy_config()
    
    # 设置默认超时
    if timeout is None:
        timeout = 600  # 默认10分钟超时
    
    # 构建客户端参数
    client_kwargs = {
        "timeout": timeout,
        **kwargs
    }
    
    # 如果有代理配置，添加到客户端参数中
    if proxies:
        client_kwargs["proxies"] = proxies
        
        # 记录使用的代理信息（隐藏认证信息）
        proxy_info = {}
        for protocol, proxy_url in proxies.items():
            # 隐藏用户名和密码
            if "@" in proxy_url:
                # 格式: protocol://user:pass@host:port
                parts = proxy_url.split("@")
                if len(parts) >= 2:
                    protocol_part = parts[0].split("://")[0] if "://" in parts[0] else "unknown"
                    host_part = "@".join(parts[1:])
                    proxy_info[protocol] = f"{protocol_part}://***:***@{host_part}"
                else:
                    proxy_info[protocol] = proxy_url
            else:
                proxy_info[protocol] = proxy_url
        
        log('info', f"使用代理配置: {proxy_info}")
    
    return httpx.AsyncClient(**client_kwargs)


def log_proxy_status():
    """
    记录当前代理配置状态
    """
    proxy_config = get_proxy_config()
    if proxy_config:
        # 隐藏认证信息后记录
        safe_config = {}
        for protocol, proxy_url in proxy_config.items():
            if "@" in proxy_url and "://" in proxy_url:
                scheme_auth, host_port = proxy_url.split("@", 1)
                scheme = scheme_auth.split("://")[0]
                safe_config[protocol] = f"{scheme}://***:***@{host_port}"
            else:
                safe_config[protocol] = proxy_url
        log('info', f"代理配置已启用: {safe_config}")
    else:
        log('info', "未配置代理，使用直连")