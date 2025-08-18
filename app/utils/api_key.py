import random
import re
import os
import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.logging import format_log_message
import app.config.settings as settings
logger = logging.getLogger("my_logger")

class APIKeyManager:
    def __init__(self):
        # 检查是否启用存储，如果禁用存储则跳过格式检查
        if settings.ENABLE_STORAGE:
            # 启用存储时使用严格格式检查（保持原逻辑）
            self.api_keys = re.findall(
                r"AIzaSy[a-zA-Z0-9_-]{33}", settings.GEMINI_API_KEYS)
        else:
            # 禁用存储时使用宽松解析（解决当前问题）
            self.api_keys = [key.strip() for key in settings.GEMINI_API_KEYS.split(',') if key.strip()]
        
        # 加载更多 GEMINI_API_KEYS，应用同样的逻辑
        for i in range(1, 99):
            if keys := os.environ.get(f"GEMINI_API_KEYS_{i}", ""):
                if settings.ENABLE_STORAGE:
                    self.api_keys += re.findall(r"AIzaSy[a-zA-Z0-9_-]{33}", keys)
                else:
                    self.api_keys += [key.strip() for key in keys.split(',') if key.strip()]
            else:
                break

        self.key_stack = [] # 初始化密钥栈
        self._reset_key_stack() # 初始化时创建随机密钥栈
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.lock = asyncio.Lock() # Added lock

    def _reset_key_stack(self):
        """创建并随机化密钥栈"""
        shuffled_keys = self.api_keys[:]  # 创建 api_keys 的副本以避免直接修改原列表
        random.shuffle(shuffled_keys)
        self.key_stack = shuffled_keys

    async def add_successful_client_key(self, client_key: str):
        """在请求成功后将客户端密钥添加到池中（去重），并持久化保存"""
        async with self.lock:
            if client_key not in self.api_keys:
                # 添加到内存中的密钥池
                self.api_keys.append(client_key)
                self._reset_key_stack()
                
                # 更新settings中的GEMINI_API_KEYS并持久化
                current_keys = settings.GEMINI_API_KEYS.split(',') if settings.GEMINI_API_KEYS else []
                current_keys = [key.strip() for key in current_keys if key.strip()]
                
                if client_key not in current_keys:
                    current_keys.append(client_key)
                    settings.GEMINI_API_KEYS = ','.join(current_keys)
                    
                    # 调用持久化保存
                    try:
                        from app.config.persistence import save_settings
                        save_settings()
                        log_msg = format_log_message('INFO', f"已添加成功验证的客户端API密钥到池中并持久化: {client_key[:8]}...")
                        logger.info(log_msg)
                    except Exception as e:
                        log_msg = format_log_message('WARNING', f"客户端API密钥已添加到内存池，但持久化失败: {str(e)}")
                        logger.warning(log_msg)
                
                return True
            return False

    async def get_available_key(self, priority_key: str = None):
        """从栈顶获取密钥，若栈空则重新生成
        
        实现负载均衡：
        1. 维护一个随机排序的栈存储apikey
        2. 每次调用从栈顶取出一个key返回
        3. 栈空时重新随机生成栈
        4. 确保异步和并发安全
        5. 支持优先密钥，如果提供则直接返回
        """
        # 如果有优先密钥，直接返回
        if priority_key:
            return priority_key
            
        async with self.lock:
            # 如果栈为空，重新生成
            if not self.key_stack:
                self._reset_key_stack()
            
            # 从栈顶取出key
            if self.key_stack:
                return self.key_stack.pop()
            
            # 如果没有可用的API密钥，记录错误
            if not self.api_keys:
                log_msg = format_log_message('ERROR', "没有配置任何 API 密钥！")
                logger.error(log_msg)
            log_msg = format_log_message('ERROR', "没有可用的API密钥！")
            logger.error(log_msg)
            return None

    def show_all_keys(self):
        log_msg = format_log_message('INFO', f"当前可用API key个数: {len(self.api_keys)} ")
        logger.info(log_msg)
        for i, api_key in enumerate(self.api_keys):
            log_msg = format_log_message('INFO', f"API Key{i}: {api_key[:8]}...{api_key[-3:]}")
            logger.info(log_msg)

    # def blacklist_key(self, key):
    #     log_msg = format_log_message('WARNING', f"{key[:8]} → 暂时禁用 {self.api_key_blacklist_duration} 秒")
    #     logger.warning(log_msg)
    #     self.api_key_blacklist.add(key)
    #     self.scheduler.add_job(lambda: self.api_key_blacklist.discard(key), 'date',
    #                            run_date=datetime.now() + timedelta(seconds=self.api_key_blacklist_duration))

async def test_api_key(api_key: str) -> bool:
    """
    测试 API 密钥是否有效。
    """
    try:
        import httpx
        import app.config.settings as settings
        from app.utils.http_client import create_http_client
        url = "{}/v1beta/models?key={}".format(settings.GEMINI_API_BASE_URL, api_key)
        async with create_http_client() as client:
            response = await client.get(url)
            response.raise_for_status()
            return True
    except Exception:
        return False
