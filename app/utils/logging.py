import logging
from datetime import datetime
from collections import deque
from threading import Lock

DEBUG = False  # 可以从环境变量中获取

LOG_FORMAT_DEBUG = '%(asctime)s - %(levelname)s - [%(key)s]-%(request_type)s-[%(model)s]-%(status_code)s: %(message)s - %(error_message)s'
LOG_FORMAT_NORMAL = '[%(asctime)s] [%(levelname)s] [%(key)s]-%(request_type)s-[%(model)s]-%(status_code)s: %(message)s'

# Vertex日志格式
VERTEX_LOG_FORMAT_DEBUG = '%(asctime)s - %(levelname)s - [%(vertex_id)s]-%(operation)s-[%(status)s]: %(message)s - %(error_message)s'
VERTEX_LOG_FORMAT_NORMAL = '[%(asctime)s] [%(levelname)s] [%(vertex_id)s]-%(operation)s-[%(status)s]: %(message)s'

# 配置 logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# 控制台处理器
console_handler = logging.StreamHandler() 

# 设置日志格式
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter) 
logger.addHandler(console_handler)

# 日志缓存，用于在网页上显示最近的日志
class LogManager:
    def __init__(self, max_logs=100):
        self.logs = deque(maxlen=max_logs)  # 使用双端队列存储最近的日志
        self.lock = Lock()
    
    def add_log(self, log_entry):
        with self.lock:
            self.logs.append(log_entry)
    
    def get_recent_logs(self, count=50):
        with self.lock:
            return list(self.logs)[-count:]

# 创建日志管理器实例 (输出到前端)
log_manager = LogManager()

# Vertex日志缓存，用于在网页上显示最近的Vertex日志
class VertexLogManager:
    def __init__(self, max_logs=100):
        self.logs = deque(maxlen=max_logs)  # 使用双端队列存储最近的Vertex日志
        self.lock = Lock()
    
    def add_log(self, log_entry):
        with self.lock:
            self.logs.append(log_entry)
    
    def get_recent_logs(self, count=50):
        with self.lock:
            return list(self.logs)[-count:]

# 创建Vertex日志管理器实例 (输出到前端)
vertex_log_manager = VertexLogManager()

def format_log_message(level, message, extra=None):
    extra = extra or {}
    log_values = {
        'asctime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'levelname': level,
        'key': extra.get('key', ''),
        'request_type': extra.get('request_type', ''),
        'model': extra.get('model', ''),
        'status_code': extra.get('status_code', ''),
        'error_message': extra.get('error_message', ''),
        'message': message
    }
    log_format = LOG_FORMAT_DEBUG if DEBUG else LOG_FORMAT_NORMAL
    formatted_log = log_format % log_values
    
    # 将格式化后的日志添加到日志管理器
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'level': level,
        'key': extra.get('key', ''),
        'request_type': extra.get('request_type', ''),
        'model': extra.get('model', ''),
        'status_code': extra.get('status_code', ''),
        'message': message,
        'error_message': extra.get('error_message', ''),
        'formatted': formatted_log
    }
    log_manager.add_log(log_entry)
    
    return formatted_log

def vertex_format_log_message(level, message, extra=None):
    extra = extra or {}
    log_values = {
        'asctime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'levelname': level,
        'vertex_id': extra.get('vertex_id', ''),
        'operation': extra.get('operation', ''),
        'status': extra.get('status', ''),
        'error_message': extra.get('error_message', ''),
        'message': message
    }
    log_format = VERTEX_LOG_FORMAT_DEBUG if DEBUG else VERTEX_LOG_FORMAT_NORMAL
    formatted_log = log_format % log_values
    
    # 将格式化后的Vertex日志添加到Vertex日志管理器
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'level': level,
        'vertex_id': extra.get('vertex_id', ''),
        'operation': extra.get('operation', ''),
        'status': extra.get('status', ''),
        'message': message,
        'error_message': extra.get('error_message', ''),
        'formatted': formatted_log
    }
    vertex_log_manager.add_log(log_entry)
    
    return formatted_log
    
    
def log(level: str, message: str, extra: dict = None, **kwargs):
    final_extra = {}
    
    if extra is not None and isinstance(extra, dict):
        final_extra.update(extra)
    
    # 将 kwargs 中的其他关键字参数合并进来，kwargs 会覆盖 extra 中的同名键
    final_extra.update(kwargs)
    
    # 调用 format_log_message，传递合并后的 final_extra 字典
    msg = format_log_message(level.upper(), message, extra=final_extra)
    
    getattr(logger, level.lower())(msg)

def vertex_log(level: str, message: str, extra: dict = None, **kwargs):
    final_extra = {}
    
    if extra is not None and isinstance(extra, dict):
        final_extra.update(extra)
    
    # 将 kwargs 中的其他关键字参数合并进来，kwargs 会覆盖 extra 中的同名键
    final_extra.update(kwargs)
    
    # 调用 vertex_format_log_message，传递合并后的 final_extra 字典
    msg = vertex_format_log_message(level.upper(), message, extra=final_extra)
    
    getattr(logger, level.lower())(msg)


def log_upstream_response(response_data, api_key, model, request_type="gemini"):
    """
    动态记录上游API响应
    
    Args:
        response_data: 上游API返回的完整响应数据
        api_key: API密钥（将被脱敏显示）
        model: 使用的模型名称
        request_type: 请求类型（如complete_chat、stream_chat等）
    """
    import os
    import json
    import app.config.settings as settings
    
    # 动态读取LOG_UPSTREAM_RESPONSES环境变量
    log_enabled = os.environ.get("LOG_UPSTREAM_RESPONSES", "false").lower() in ["true", "1", "yes"]
    if not log_enabled:
        return
    
    try:
        # 生成精确到毫秒的时间戳：YYYYMMDDHHMMSSMMM
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # %f是微秒，取前3位变成毫秒
        
        # 构建完整的日志内容
        log_content = {
            "timestamp": timestamp,
            "api_key": api_key[:8] + "..." if api_key else "unknown",
            "model": model,
            "request_type": request_type,
            "response": response_data  # 完整的response数据
        }
        
        # 使用启动时的ENABLE_STORAGE配置（不动态读取）
        if settings.ENABLE_STORAGE:
            # 输出到文件：response-YYYYMMDDHHMMSSMMM.json
            filename = f"response-{timestamp}.json"
            filepath = os.path.join(settings.STORAGE_DIR, filename)
            
            try:
                os.makedirs(settings.STORAGE_DIR, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(log_content, f, ensure_ascii=False, indent=2)
            except Exception as e:
                # 如果文件写入失败，降级到控制台输出
                print(f"UPSTREAM_RESPONSE_FILE_ERROR: {e}")
                print(f"UPSTREAM_RESPONSE: {json.dumps(log_content, ensure_ascii=False)}")
        else:
            # 输出到控制台（docker日志）
            print(f"UPSTREAM_RESPONSE: {json.dumps(log_content, ensure_ascii=False)}")
            
    except Exception as e:
        # 确保日志记录不会影响主要业务流程
        print(f"UPSTREAM_RESPONSE_LOG_ERROR: {e}")


# 全局变量存储活跃的流式请求日志
_active_stream_logs = {}

def log_stream_request_start(api_key, model):
    """
    开始流式请求时调用，创建累积日志
    
    Args:
        api_key: API密钥
        model: 模型名称
        
    Returns:
        str: 唯一的请求ID
    """
    import uuid
    import os
    
    # 动态检查环境变量，如果未启用则直接返回None
    log_enabled = os.environ.get("LOG_UPSTREAM_RESPONSES", "false").lower() in ["true", "1", "yes"]
    if not log_enabled:
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        request_id = f"stream-{timestamp}-{uuid.uuid4().hex[:6]}"
        
        # 初始化流式请求日志
        _active_stream_logs[request_id] = {
            "request_info": {
                "request_id": request_id,
                "timestamp": timestamp,
                "api_key": api_key[:8] + "..." if api_key else "unknown",
                "model": model,
                "request_type": "stream_chat"
            },
            "chunks": [],
            "start_time": datetime.now()
        }
        
        return request_id
        
    except Exception as e:
        print(f"STREAM_LOG_START_ERROR: {e}")
        return None


def log_stream_chunk(request_id, chunk_data):
    """
    记录流式响应的单个chunk
    
    Args:
        request_id: 请求ID（由log_stream_request_start返回）
        chunk_data: chunk的完整数据
    """
    if not request_id or request_id not in _active_stream_logs:
        return
        
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        chunk_info = {
            "chunk_index": len(_active_stream_logs[request_id]["chunks"]),
            "timestamp": timestamp,
            "data": chunk_data
        }
        
        _active_stream_logs[request_id]["chunks"].append(chunk_info)
        
    except Exception as e:
        print(f"STREAM_LOG_CHUNK_ERROR: {e}")


def log_stream_request_end(request_id):
    """
    结束流式请求时调用，完成日志记录并输出
    
    Args:
        request_id: 请求ID（由log_stream_request_start返回）
    """
    if not request_id or request_id not in _active_stream_logs:
        return
        
    try:
        log_data = _active_stream_logs[request_id]
        end_time = datetime.now()
        
        # 添加汇总信息
        log_data["summary"] = {
            "total_chunks": len(log_data["chunks"]),
            "start_time": log_data["start_time"].strftime("%Y%m%d%H%M%S%f")[:-3],
            "end_time": end_time.strftime("%Y%m%d%H%M%S%f")[:-3],
            "duration_ms": int((end_time - log_data["start_time"]).total_seconds() * 1000)
        }
        
        # 移除临时字段
        del log_data["start_time"]
        
        # 再次动态检查环境变量（防止运行期间被改变）
        import os
        log_enabled = os.environ.get("LOG_UPSTREAM_RESPONSES", "false").lower() in ["true", "1", "yes"]
        if not log_enabled:
            # 清理内存
            del _active_stream_logs[request_id]
            return
        
        import app.config.settings as settings
        import json
        
        if settings.ENABLE_STORAGE:
            # 输出到文件
            filename = f"{request_id}.json"
            filepath = os.path.join(settings.STORAGE_DIR, filename)
            
            os.makedirs(settings.STORAGE_DIR, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        else:
            # 输出到控制台
            print(f"UPSTREAM_STREAM_RESPONSE: {json.dumps(log_data, ensure_ascii=False)}")
            
    except Exception as e:
        print(f"STREAM_LOG_END_ERROR: {e}")
    finally:
        # 清理内存
        if request_id in _active_stream_logs:
            del _active_stream_logs[request_id]