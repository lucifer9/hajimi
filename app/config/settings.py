import os
import pathlib
import logging
from datetime import datetime, timedelta
import asyncio

# ---------- 以下是基础配置信息 ----------

# 定义需要合并环境变量和settings.json的配置项
MERGE_CONFIGS = {
    'SPECIFIC_TAGS_TO_CHECK', 
    'REQUIRED_TAGS', 
    'GEMINI_API_KEYS', 
    'INVALID_API_KEYS', 
    'ALLOWED_ORIGINS'
}

def get_env_value(key, default_value, value_type=str):
    """从环境变量获取配置值，支持类型转换"""
    env_value = os.environ.get(key, default_value)
    if value_type == bool:
        return env_value.lower() in ["true", "1", "yes"]
    elif value_type == int:
        return int(env_value)
    elif value_type == float:
        return float(env_value)
    else:
        return env_value

# 服务器监听地址和端口配置（不可通过Web配置）
HOST = get_env_value("HOST", "0.0.0.0")
PORT = get_env_value("PORT", "7860", int)

# API上游地址配置（可通过Web配置，settings.json优先）
GEMINI_API_BASE_URL = get_env_value("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com")
VERTEX_API_BASE_URL = get_env_value("VERTEX_API_BASE_URL", "https://aiplatform.googleapis.com")

# 代理配置（可通过Web配置，settings.json优先）
HTTP_PROXY = get_env_value("HTTP_PROXY", "")
HTTPS_PROXY = get_env_value("HTTPS_PROXY", "")
SOCKS_PROXY = get_env_value("SOCKS_PROXY", "")
ALL_PROXY = get_env_value("ALL_PROXY", "")

# 调用本项目时使用的密码（不可通过Web配置）
PASSWORD = get_env_value("PASSWORD", "123").strip('"')

# 网页配置密码，设置后，在网页修改配置时使用 WEB_PASSWORD 而不是上面的 PASSWORD（不可通过Web配置）
WEB_PASSWORD = get_env_value("WEB_PASSWORD", PASSWORD).strip('"')

# API密钥（合并配置：环境变量 + settings.json）
GEMINI_API_KEYS = get_env_value("GEMINI_API_KEYS", "")

# 假流式是否开启（可通过Web配置，settings.json优先）
FAKE_STREAMING = get_env_value("FAKE_STREAMING", "true", bool)

# Encrypt-Full功能配置（可通过Web配置，settings.json优先）
ENABLE_ENCRYPT_FULL_SUFFIX = get_env_value("ENABLE_ENCRYPT_FULL_SUFFIX", "true", bool)

# 原生Gemini API是否默认启用encrypt-full模式（可通过Web配置，settings.json优先）
NATIVE_API_ENCRYPT_FULL = get_env_value("NATIVE_API_ENCRYPT_FULL", "false", bool)

# 配置持久化存储目录（不可通过Web配置）
STORAGE_DIR = get_env_value("STORAGE_DIR", "/hajimi/settings/")
ENABLE_STORAGE = get_env_value("ENABLE_STORAGE", "false", bool)

# 并发请求配置（可通过Web配置，settings.json优先）
CONCURRENT_REQUESTS = get_env_value("CONCURRENT_REQUESTS", "1", int)  # 默认并发请求数
INCREASE_CONCURRENT_ON_FAILURE = get_env_value("INCREASE_CONCURRENT_ON_FAILURE", "0", int)  # 失败时增加的并发数
MAX_CONCURRENT_REQUESTS = get_env_value("MAX_CONCURRENT_REQUESTS", "3", int)  # 最大并发请求数

# 缓存配置（可通过Web配置，settings.json优先）
CACHE_EXPIRY_TIME = get_env_value("CACHE_EXPIRY_TIME", "21600", int)  # 默认缓存 6 小时 (21600 秒)
MAX_CACHE_ENTRIES = get_env_value("MAX_CACHE_ENTRIES", "500", int)  # 默认最多缓存500条响应
CALCULATE_CACHE_ENTRIES = get_env_value("CALCULATE_CACHE_ENTRIES", "6", int)  # 默认取最后 6 条消息算缓存键
PRECISE_CACHE = get_env_value("PRECISE_CACHE", "false", bool)  # 是否取所有消息来算缓存键

# 是否启用 Vertex AI（可通过Web配置，settings.json优先）
ENABLE_VERTEX = get_env_value("ENABLE_VERTEX", "false", bool)
GOOGLE_CREDENTIALS_JSON = get_env_value("GOOGLE_CREDENTIALS_JSON", "")

# 是否启用快速模式 Vertex（可通过Web配置，settings.json优先）
ENABLE_VERTEX_EXPRESS = get_env_value("ENABLE_VERTEX_EXPRESS", "false", bool)
VERTEX_EXPRESS_API_KEY = get_env_value("VERTEX_EXPRESS_API_KEY", "")

# 联网搜索配置（可通过Web配置，settings.json优先）
search={
    "search_mode": get_env_value("SEARCH_MODE", "false", bool),
    "search_prompt": get_env_value("SEARCH_PROMPT", "（使用搜索工具联网搜索，需要在content中结合搜索内容）").strip('"')
}

# 随机字符串（可通过Web配置，settings.json优先）
RANDOM_STRING = get_env_value("RANDOM_STRING", "true", bool)
RANDOM_STRING_LENGTH = get_env_value("RANDOM_STRING_LENGTH", "5", int)

# 空响应重试次数限制（可通过Web配置，settings.json优先）
MAX_EMPTY_RESPONSES = get_env_value("MAX_EMPTY_RESPONSES", "5", int)  # 默认最多允许5次空响应

# 未闭合标签重试次数限制（向后兼容，内部统一使用MAX_RETRY_NUM）
MAX_UNCLOSED_TAG_RETRIES = get_env_value("MAX_UNCLOSED_TAG_RETRIES", "5", int)  # 默认最多允许5次未闭合标签重试

# 响应长度检测配置（可通过Web配置，settings.json优先）
MIN_RESPONSE_LENGTH = get_env_value("MIN_RESPONSE_LENGTH", "100", int)  # 默认最短响应长度

# 上游响应日志记录配置（内存缓存，避免每次都读取环境变量）
LOG_UPSTREAM_RESPONSES_ENABLED = get_env_value("LOG_UPSTREAM_RESPONSES", "false", bool)

# 指定标签闭合检测配置（可通过Web配置，settings.json优先）
ENABLE_SPECIFIC_TAG_DETECTION = get_env_value("ENABLE_SPECIFIC_TAG_DETECTION", "false", bool)

# 需要检测闭合的特定标签配置（合并配置：环境变量 + settings.json）
SPECIFIC_TAGS_TO_CHECK_STR = get_env_value("SPECIFIC_TAGS_TO_CHECK", "assess,your_choice,Status_block,tableThink,tableEdit,abstract,UpdateVariable,INDRS,details,think,thinking")
SPECIFIC_TAGS_TO_CHECK = [tag.strip() for tag in SPECIFIC_TAGS_TO_CHECK_STR.split(',') if tag.strip()]

# 必须标签检测配置（可通过Web配置，settings.json优先）
ENABLE_REQUIRED_TAG_DETECTION = get_env_value("ENABLE_REQUIRED_TAG_DETECTION", "false", bool)

# 必须出现且正确闭合的标签配置（合并配置：环境变量 + settings.json）
REQUIRED_TAGS_STR = get_env_value("REQUIRED_TAGS", "")
REQUIRED_TAGS = [tag.strip() for tag in REQUIRED_TAGS_STR.split(',') if tag.strip()]

# ---------- 以下是其他配置信息 ----------

# 访问限制（可通过Web配置，settings.json优先）
MAX_RETRY_NUM = get_env_value("MAX_RETRY_NUM", "15", int)  # 请求时的最大总轮询 key 数
MAX_REQUESTS_PER_MINUTE = get_env_value("MAX_REQUESTS_PER_MINUTE", "30", int)
MAX_REQUESTS_PER_DAY_PER_IP = get_env_value("MAX_REQUESTS_PER_DAY_PER_IP", "600", int)

# API密钥使用限制（可通过Web配置，settings.json优先）
API_KEY_DAILY_LIMIT = get_env_value("API_KEY_DAILY_LIMIT", "100", int)  # 默认每个API密钥每24小时可使用100次

# 模型屏蔽黑名单，格式应为逗号分隔的模型名称集合（不可通过Web配置）
BLOCKED_MODELS = { model.strip() for model in get_env_value("BLOCKED_MODELS", "").split(",") if model.strip() }

# 公益站模式（不可通过Web配置）
PUBLIC_MODE = get_env_value("PUBLIC_MODE", "false", bool)
# 前端地址（不可通过Web配置）
DASHBOARD_URL = get_env_value("DASHBOARD_URL", "")

# 模型屏蔽白名单（不可通过Web配置）
WHITELIST_MODELS = { x.strip() for x in get_env_value("WHITELIST_MODELS", "").split(",") if x.strip() }
# 白名单User-Agent（不可通过Web配置）
WHITELIST_USER_AGENT = { x.strip().lower() for x in get_env_value("WHITELIST_USER_AGENT", "").split(",") if x.strip() }

# 跨域配置（合并配置：环境变量 + settings.json）
# 允许的源列表，逗号分隔，例如 "http://localhost:3000,https://example.com"
ALLOWED_ORIGINS_STR = get_env_value("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",") if origin.strip()]

# ---------- 运行时全局信息，无需修改 ----------

# 基础目录设置
BASE_DIR = pathlib.Path(__file__).parent.parent

# 失效的API密钥（合并配置：环境变量 + settings.json）
INVALID_API_KEYS = get_env_value("INVALID_API_KEYS", "")

version={
    "local_version":"0.0.0",
    "remote_version":"0.0.0",
    "has_update":False
}

# API调用统计
# 这个对象保留为空结构以保持向后兼容性
# 实际统计数据已迁移到 app/utils/stats.py 中的 ApiStatsManager 类
api_call_stats = {
    'calls': []  # 兼容旧版代码结构
}

# 用于保护 api_call_stats 并发访问的锁
stats_lock = asyncio.Lock()

# 日志配置
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True


# ---------- 以下配置信息已废弃 ----------

# 假流式请求的空内容返回间隔（秒）
FAKE_STREAMING_INTERVAL = get_env_value("FAKE_STREAMING_INTERVAL", "1", float)
# 假流式响应的每个块大小
FAKE_STREAMING_CHUNK_SIZE = get_env_value("FAKE_STREAMING_CHUNK_SIZE", "10", int)
# 假流式响应的每个块之间的延迟（秒）
FAKE_STREAMING_DELAY_PER_CHUNK = get_env_value("FAKE_STREAMING_DELAY_PER_CHUNK", "0.1", float)

# 非流式请求TCP保活配置
NONSTREAM_KEEPALIVE_ENABLED = get_env_value("NONSTREAM_KEEPALIVE_ENABLED", "true", bool)
NONSTREAM_KEEPALIVE_INTERVAL = get_env_value("NONSTREAM_KEEPALIVE_INTERVAL", "5.0", float)
