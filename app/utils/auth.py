from typing import Optional, Tuple
from fastapi import HTTPException, Header, Query
import app.config.settings as settings
import re
from app.utils.api_key import test_api_key

# 自定义密码校验依赖函数
async def custom_verify_password(
    authorization: Optional[str] = Header(None, description="OpenAI 格式请求 Key, 格式: Bearer sk-xxxx"),
    x_goog_api_key: Optional[str] = Header(None, description="Gemini 格式请求 Key, 从请求头 x-goog-api-key 获取"),
    key: Optional[str] = Query(None, description="Gemini 格式请求 Key, 从查询参数 key 获取"),
    alt: Optional[str] = None
):
    """
@@ -15,22 +18,79 @@
    2. 根据类型，与项目配置的密钥进行比对。
    3. 如果 Key 无效、缺失或不匹配，则抛出 HTTPException。
    """
    client_provided_api_key: Optional[str] = None

    # 提取客户端提供的 Key 
    if x_goog_api_key: 
        client_provided_api_key = x_goog_api_key
    elif key:
        client_provided_api_key = key
    elif authorization and authorization.startswith("Bearer "): 
        token = authorization.split(" ", 1)[1]
        client_provided_api_key = token

    # 进行校验和比对
    if (not client_provided_api_key) or (client_provided_api_key != settings.PASSWORD) :
            raise HTTPException(
                status_code=401, detail="Unauthorized: Invalid token")

# Gemini 专用认证函数
async def verify_gemini_auth(
    x_goog_api_key: Optional[str] = Header(None, description="Gemini 格式请求 Key, 从请求头 x-goog-api-key 获取"),
    key: Optional[str] = Query(None, description="Gemini 格式请求 Key, 从查询参数 key 获取")
) -> Tuple[str, Optional[str]]:
    """
    Gemini 格式请求的专用认证函数
    返回元组: (auth_type, client_key)
    auth_type: "gemini_key" 或 "password"
    client_key: 客户端提供的 API key（仅当 auth_type="gemini_key" 时）
    """
    # 提取客户端提供的key
    client_key = x_goog_api_key or key
    
    if client_key:
        # 检测是否为 Gemini API key 格式
        if re.match(r"AIzaSy[a-zA-Z0-9_-]{33}", client_key):
            # 验证 API key 有效性
            if await test_api_key(client_key):
                return ("gemini_key", client_key)
            else:
                raise HTTPException(status_code=401, detail="Invalid Gemini API key")
        
        # 检查是否为预设密码
        elif client_key == settings.PASSWORD:
            return ("password", None)
    
    raise HTTPException(status_code=401, detail="Invalid authentication for Gemini request")

def verify_web_password(password:str):
    if password != settings.WEB_PASSWORD:
        return False
    return True