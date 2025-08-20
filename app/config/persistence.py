import json
import os
import inspect
import pathlib
from app.config import settings
from app.utils.logging import log

# 定义不应该被保存或加载的配置项
EXCLUDED_SETTINGS = [
    "STORAGE_DIR", 
    "ENABLE_STORAGE", 
    "BASE_DIR", 
    "PASSWORD", 
    "WEB_PASSWORD", 
    "WHITELIST_MODELS", 
    "BLOCKED_MODELS", 
    "DEFAULT_BLOCKED_MODELS", 
    "PUBLIC_MODE", 
    "DASHBOARD_URL",
    "version",
    # 服务器启动配置（通过Web界面修改无意义）
    "HOST",
    "PORT",
    # 字符串形式的重复配置（已有对应的数组形式）
    "REQUIRED_TAGS_STR",
    "SPECIFIC_TAGS_TO_CHECK_STR", 
    "ALLOWED_ORIGINS_STR"
    # 注意：网络配置（代理和API基础URL）现在支持Web界面配置，已从排除列表中移除
]

def save_settings():
    """
    将settings中所有的从os.environ.get获取的配置保存到JSON文件中，
    但排除特定的配置项
    """
    if settings.ENABLE_STORAGE:
        # 确保存储目录存在
        storage_dir = pathlib.Path(settings.STORAGE_DIR)
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置JSON文件路径
        settings_file = storage_dir / "settings.json"
        
        # 获取settings模块中的所有变量
        settings_dict = {}
        for name, value in inspect.getmembers(settings):
            # 跳过内置和私有变量，以及函数/模块/类，以及排除列表中的配置项
            if (not name.startswith('_') and 
                not inspect.isfunction(value) and 
                not inspect.ismodule(value) and 
                not inspect.isclass(value) and
                name not in EXCLUDED_SETTINGS):
                
                # 尝试将可序列化的值添加到字典中
                try:
                    json.dumps({name: value})  # 测试是否可序列化
                    settings_dict[name] = value
                except (TypeError, OverflowError):
                    # 如果不可序列化，则跳过
                    continue
        log('info', f"保存设置到JSON文件: {settings_file}")
        
        # 保存到JSON文件
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=4)
        
        return settings_file

def merge_list_config(env_value, json_value, separator=','):
    """合并环境变量和settings.json中的列表配置"""
    # 从环境变量解析
    env_items = []
    if env_value:
        env_items = [item.strip() for item in env_value.split(separator) if item.strip()]
    
    # 从JSON解析
    json_items = []
    if json_value:
        json_items = [item.strip() for item in json_value.split(separator) if item.strip()]
    
    # 合并去重，保持顺序
    all_items = []
    seen = set()
    
    # 先添加环境变量的项目
    for item in env_items:
        if item not in seen:
            all_items.append(item)
            seen.add(item)
    
    # 再添加JSON的项目
    for item in json_items:
        if item not in seen:
            all_items.append(item)
            seen.add(item)
    
    return separator.join(all_items)

def load_settings():
    """
    从JSON文件中加载设置并更新settings模块
    新逻辑：settings.json优先，5个特殊配置项进行合并
    """
    if settings.ENABLE_STORAGE:
        # 设置JSON文件路径
        storage_dir = pathlib.Path(settings.STORAGE_DIR)
        settings_file = storage_dir / "settings.json"
        
        # 如果文件不存在，则返回
        if not settings_file.exists():
            return False
        
        # 从JSON文件中加载设置
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            
            # 更新settings模块中的变量，但排除特定配置项
            for name, value in loaded_settings.items():
                if hasattr(settings, name) and name not in EXCLUDED_SETTINGS:
                    # 对于需要合并的配置项
                    if name in settings.MERGE_CONFIGS:
                        # 获取当前环境变量值，注意不同配置项可能有不同的属性名
                        if name == "SPECIFIC_TAGS_TO_CHECK":
                            current_value = getattr(settings, "SPECIFIC_TAGS_TO_CHECK_STR", "")
                        elif name == "REQUIRED_TAGS":
                            current_value = getattr(settings, "REQUIRED_TAGS_STR", "")
                        elif name == "ALLOWED_ORIGINS":
                            current_value = getattr(settings, "ALLOWED_ORIGINS_STR", "")
                        else:
                            current_value = getattr(settings, name, "")
                        
                        # 执行合并
                        merged_value = merge_list_config(current_value, value)
                        
                        # 根据不同配置项设置相应的属性
                        if name == "SPECIFIC_TAGS_TO_CHECK":
                            setattr(settings, "SPECIFIC_TAGS_TO_CHECK_STR", merged_value)
                            setattr(settings, "SPECIFIC_TAGS_TO_CHECK", [tag.strip() for tag in merged_value.split(',') if tag.strip()])
                        elif name == "REQUIRED_TAGS":
                            setattr(settings, "REQUIRED_TAGS_STR", merged_value)
                            setattr(settings, "REQUIRED_TAGS", [tag.strip() for tag in merged_value.split(',') if tag.strip()])
                        elif name == "ALLOWED_ORIGINS":
                            setattr(settings, "ALLOWED_ORIGINS_STR", merged_value)
                            setattr(settings, "ALLOWED_ORIGINS", [origin.strip() for origin in merged_value.split(',') if origin.strip()])
                        else:
                            # 对于GEMINI_API_KEYS和INVALID_API_KEYS直接合并
                            setattr(settings, name, merged_value)
                        
                        log('info', f"合并配置 {name}: 环境变量={current_value} + JSON={value} = {merged_value}")
                    
                    # 特殊处理GOOGLE_CREDENTIALS_JSON，settings.json优先但环境变量不为空时保留
                    elif name == "GOOGLE_CREDENTIALS_JSON":
                        current_value = getattr(settings, name, "")
                        # 检查当前环境变量值是否为空
                        is_empty = (not current_value or 
                                   not current_value.strip() or 
                                   current_value.strip() in ['""', "''"])
                        if is_empty:
                            # 环境变量为空，使用settings.json的值
                            setattr(settings, name, value)
                            if value:
                                os.environ["GOOGLE_CREDENTIALS_JSON"] = value
                                log('info', f"从settings.json加载了GOOGLE_CREDENTIALS_JSON配置")
                        else:
                            # 环境变量不为空，settings.json优先
                            setattr(settings, name, value)
                            if value:
                                os.environ["GOOGLE_CREDENTIALS_JSON"] = value
                                log('info', f"settings.json优先：更新GOOGLE_CREDENTIALS_JSON配置")
                            else:
                                log('info', f"settings.json为空，保留环境变量GOOGLE_CREDENTIALS_JSON")
                    
                    # 特殊处理VERTEX_EXPRESS_API_KEY，settings.json优先
                    elif name == "VERTEX_EXPRESS_API_KEY":
                        setattr(settings, name, value)
                        if value:
                            os.environ["VERTEX_EXPRESS_API_KEY"] = value
                            log('info', f"settings.json优先：更新VERTEX_EXPRESS_API_KEY配置")
                        else:
                            log('info', f"settings.json为空，清空VERTEX_EXPRESS_API_KEY")
                    
                    # 其他配置项：settings.json优先
                    else:
                        setattr(settings, name, value)
                        log('debug', f"settings.json优先：{name} = {value}")
            
            # 在加载完设置后，检查是否需要刷新模型配置
            try:
                # 如果加载了Google Credentials JSON或Vertex Express API Key，需要刷新模型配置
                if (hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') and settings.GOOGLE_CREDENTIALS_JSON) or \
                   (hasattr(settings, 'VERTEX_EXPRESS_API_KEY') and settings.VERTEX_EXPRESS_API_KEY):
                    log('info', "检测到Google Credentials JSON或Vertex Express API Key，准备更新配置")
                    
                    # 更新配置
                    import app.vertex.config as app_config
                    
                    # 重新加载vertex配置
                    app_config.reload_config()
                    
                    # 更新app_config中的GOOGLE_CREDENTIALS_JSON
                    if hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') and settings.GOOGLE_CREDENTIALS_JSON:
                        app_config.GOOGLE_CREDENTIALS_JSON = settings.GOOGLE_CREDENTIALS_JSON
                        # 同时更新环境变量，确保其他模块能够访问到
                        os.environ["GOOGLE_CREDENTIALS_JSON"] = settings.GOOGLE_CREDENTIALS_JSON
                        log('info', "已更新app_config和环境变量中的GOOGLE_CREDENTIALS_JSON")
                    
                    # 更新app_config中的VERTEX_EXPRESS_API_KEY_VAL
                    if hasattr(settings, 'VERTEX_EXPRESS_API_KEY') and settings.VERTEX_EXPRESS_API_KEY:
                        app_config.VERTEX_EXPRESS_API_KEY_VAL = [key.strip() for key in settings.VERTEX_EXPRESS_API_KEY.split(',') if key.strip()]
                        # 同时更新环境变量
                        os.environ["VERTEX_EXPRESS_API_KEY"] = settings.VERTEX_EXPRESS_API_KEY
                        log('info', f"已更新app_config和环境变量中的VERTEX_EXPRESS_API_KEY_VAL，共{len(app_config.VERTEX_EXPRESS_API_KEY_VAL)}个有效密钥")
                    
                    log('info', "配置更新完成，Vertex AI将在下次请求时重新初始化")
                    
            except Exception as e:
                log('error', f"更新配置时出错: {str(e)}")
            
            log('info', f"加载设置成功")
            return True
        except Exception as e:
            log('error', f"加载设置时出错: {e}")
            return False 