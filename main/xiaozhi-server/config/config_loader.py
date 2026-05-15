import os
import yaml
from collections.abc import Mapping
from config.manage_api_client import init_service, get_server_config, get_agent_models


def get_project_dir():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"


def read_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


def load_config():
    """加载配置文件"""
    from core.utils.cache.manager import cache_manager, CacheType

    # 检查缓存
    cached_config = cache_manager.get(CacheType.CONFIG, "main_config")
    if cached_config is not None:
        return cached_config

    default_config_path = get_project_dir() + "config.yaml"
    custom_config_path = get_project_dir() + "data/.config.yaml"

    # Support config profiles via XIAOZHI_CONFIG_PROFILE env var
    # e.g. XIAOZHI_CONFIG_PROFILE=storyteller → loads data/.config.storyteller.yaml
    profile = os.environ.get("XIAOZHI_CONFIG_PROFILE", "").strip()
    if profile:
        profile_path = get_project_dir() + f"data/.config.{profile}.yaml"
        if os.path.exists(profile_path):
            custom_config_path = profile_path
            print(f"Using config profile: {profile} ({profile_path})")
        else:
            print(f"Warning: config profile '{profile}' not found at {profile_path}, using default")

    # 加载默认配置
    default_config = read_config(default_config_path)
    custom_config = read_config(custom_config_path)

    # Cho script/CI: bỏ qua pull config từ manager-api (tránh treo khi API không chạy)
    _local_only = os.environ.get("XIAOZHI_LOCAL_CONFIG_ONLY", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    if custom_config.get("manager-api", {}).get("url") and not _local_only:
        merged_local = merge_configs(default_config, custom_config)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            config = asyncio.run_coroutine_threadsafe(
                get_config_from_api_async(merged_local), loop
            ).result()
        except RuntimeError:
            config = asyncio.run(get_config_from_api_async(merged_local))
    else:
        # 合并配置
        config = merge_configs(default_config, custom_config)
    # 初始化目录
    ensure_directories(config)

    # 缓存配置
    cache_manager.set(CacheType.CONFIG, "main_config", config)
    return config


async def get_config_from_api_async(config):
    """从Java API获取配置（异步版本）"""
    import logging
    _loader_logger = logging.getLogger("config_loader")

    # 初始化API客户端
    init_service(config)

    # 获取服务器配置
    config_data = await get_server_config()
    if config_data is None:
        raise Exception("Failed to fetch server config from API")

    # Debug: log LLM + selected_module from API response
    _api_llm = config_data.get("LLM", {})
    _api_sel = config_data.get("selected_module", {})
    _loader_logger.info("[config_loader] API selected_module = %s", _api_sel)
    _loader_logger.info("[config_loader] API LLM keys = %s", list(_api_llm.keys()) if isinstance(_api_llm, dict) else type(_api_llm))
    for _k, _v in (_api_llm.items() if isinstance(_api_llm, dict) else []):
        if isinstance(_v, dict):
            _loader_logger.info("[config_loader] LLM[%s] type=%s, has_api_key=%s, api_key_preview=%s",
                                _k, _v.get("type"), bool(_v.get("api_key")),
                                (str(_v.get("api_key",""))[:6] + "...") if _v.get("api_key") else "EMPTY")

    config_data["read_config_from_api"] = True
    config_data["manager-api"] = {
        "url": config["manager-api"].get("url", ""),
        "secret": config["manager-api"].get("secret", ""),
    }
    auth_enabled = config_data.get("server", {}).get("auth", {}).get("enabled", False)
    # server的配置以本地为准
    if config.get("server"):
        config_data["server"] = {
            "ip": config["server"].get("ip", ""),
            "port": config["server"].get("port", ""),
            "http_port": config["server"].get("http_port", ""),
            "websocket": config["server"].get("websocket", ""),
            "vision_explain": config["server"].get("vision_explain", ""),
            "auth_key": config["server"].get("auth_key", ""),
        }
    config_data["server"]["auth"] = {"enabled": auth_enabled}
    # 如果服务器没有prompt_template，则从本地配置读取
    if not config_data.get("prompt_template"):
        config_data["prompt_template"] = config.get("prompt_template")

    # Preserve local RAG plugin config when API payload doesn't include plugins/search_from_qdrant.
    # This keeps startup warmup available in API-config mode.
    local_plugins = config.get("plugins", {}) if isinstance(config.get("plugins", {}), Mapping) else {}
    local_qdrant = local_plugins.get("search_from_qdrant", {}) if isinstance(local_plugins.get("search_from_qdrant", {}), Mapping) else {}
    api_plugins = config_data.get("plugins", {}) if isinstance(config_data.get("plugins", {}), Mapping) else {}
    api_qdrant = api_plugins.get("search_from_qdrant", {}) if isinstance(api_plugins.get("search_from_qdrant", {}), Mapping) else {}

    if local_qdrant:
        if not api_plugins:
            config_data["plugins"] = {}
            api_plugins = config_data["plugins"]

        # Merge with API-first precedence; fill missing keys from local config.
        merged_qdrant = dict(local_qdrant)
        merged_qdrant.update(api_qdrant)
        api_plugins["search_from_qdrant"] = merged_qdrant

    # Preserve local RAG config (inline mode etc.) — API doesn't manage this.
    if not config_data.get("RAG") and config.get("RAG"):
        config_data["RAG"] = config["RAG"]

    # Preserve local Memory config (API doesn't manage this)
    if config.get("Memory"):
        config_data["Memory"] = config["Memory"]
    local_mem = config.get("selected_module", {}).get("Memory")
    if local_mem:
        if "selected_module" not in config_data:
            config_data["selected_module"] = {}
        config_data["selected_module"]["Memory"] = local_mem
    if config.get("long_term_memory"):
        config_data["long_term_memory"] = config["long_term_memory"]

        # Preserve local LLM config
        if config.get("LLM"):
            config_data["LLM"] = config["LLM"]
        local_llm = config.get("selected_module", {}).get("LLM")
        if local_llm:
            if "selected_module" not in config_data:
                config_data["selected_module"] = {}
            config_data["selected_module"]["LLM"] = local_llm

        # Preserve local TTS config
        if config.get("TTS"):
            config_data["TTS"] = config["TTS"]
        local_tts = config.get("selected_module", {}).get("TTS")
        if local_tts:
            if "selected_module" not in config_data:
                config_data["selected_module"] = {}
            config_data["selected_module"]["TTS"] = local_tts

    # Preserve local ASR config (API doesn't manage local ASR providers like Zipformer)
    local_asr = config.get("selected_module", {}).get("ASR")
    if local_asr:
        if "selected_module" not in config_data:
            config_data["selected_module"] = {}
        config_data["selected_module"]["ASR"] = local_asr
        local_asr_cfg = config.get("ASR", {}).get(local_asr)
        if local_asr_cfg:
            if "ASR" not in config_data:
                config_data["ASR"] = {}
            config_data["ASR"][local_asr] = local_asr_cfg

    return config_data


async def get_private_config_from_api(config, device_id, client_id):
    """从Java API获取私有配置"""
    return await get_agent_models(device_id, client_id, config["selected_module"])


def ensure_directories(config):
    """确保所有配置路径存在"""
    dirs_to_create = set()
    project_dir = get_project_dir()  # 获取项目根目录
    # 日志文件目录
    log_dir = config.get("log", {}).get("log_dir", "tmp")
    dirs_to_create.add(os.path.join(project_dir, log_dir))

    # ASR/TTS模块输出目录
    for module in ["ASR", "TTS"]:
        if config.get(module) is None:
            continue
        for provider in config.get(module, {}).values():
            output_dir = provider.get("output_dir", "")
            if output_dir:
                dirs_to_create.add(output_dir)

    # 根据selected_module创建模型目录
    selected_modules = config.get("selected_module", {})
    for module_type in ["ASR", "LLM", "TTS"]:
        selected_provider = selected_modules.get(module_type)
        if not selected_provider:
            continue
        if config.get(module) is None:
            continue
        if config.get(selected_provider) is None:
            continue
        provider_config = config.get(module_type, {}).get(selected_provider, {})
        output_dir = provider_config.get("output_dir")
        if output_dir:
            full_model_dir = os.path.join(project_dir, output_dir)
            dirs_to_create.add(full_model_dir)

    # 统一创建目录（保留原data目录创建）
    for dir_path in dirs_to_create:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except PermissionError:
            print(f"Warning: could not create directory {dir_path}; check write permissions")


def merge_configs(default_config, custom_config):
    """
    递归合并配置，custom_config优先级更高

    Args:
        default_config: 默认配置
        custom_config: 用户自定义配置

    Returns:
        合并后的配置
    """
    if not isinstance(default_config, Mapping) or not isinstance(
        custom_config, Mapping
    ):
        return custom_config

    merged = dict(default_config)

    for key, value in custom_config.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged
