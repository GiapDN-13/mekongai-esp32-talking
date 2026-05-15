import os
import sys
from loguru import logger
from config.config_loader import load_config
from config.settings import check_config_file
from datetime import datetime

SERVER_VERSION = "0.9.2"
_logger_initialized = False


def get_module_abbreviation(module_name, module_dict):
    module_value = module_dict.get(module_name, "")
    if not module_value:
        return "00"
    if "_" in module_value:
        parts = module_value.split("_")
        return parts[-1][:2] if parts[-1] else "00"
    return module_value[:2]


def build_module_string(selected_module):
    return (
        get_module_abbreviation("VAD", selected_module)
        + get_module_abbreviation("ASR", selected_module)
        + get_module_abbreviation("LLM", selected_module)
        + get_module_abbreviation("TTS", selected_module)
        + get_module_abbreviation("Memory", selected_module)
        + get_module_abbreviation("Intent", selected_module)
        + get_module_abbreviation("VLLM", selected_module)
    )


def formatter(record):
    """Filter and transform log records for console readability."""
    tag = record["extra"].get("tag", record["name"])
    record["extra"].setdefault("tag", tag)
    record["extra"].setdefault("selected_module", "00000000000000")
    record["selected_module"] = record["extra"]["selected_module"]

    parts = tag.rsplit(".", 2)
    if len(parts) >= 2:
        short = ".".join(parts[-2:])
    else:
        short = tag
    short = short.replace("plugins_func.functions.", "plug.") \
                 .replace("core.providers.", "") \
                 .replace("core.handle.", "") \
                 .replace("core.utils.", "") \
                 .replace("core.", "")
    if len(short) > 20:
        short = short[-20:]
    record["extra"]["tag_short"] = short

    msg = record["message"]

    # --- Pipeline stage labels (no emoji, CLI-friendly) ---
    if "ASR text:" in msg:
        record["extra"]["tag_short"] = "ASR"
        record["message"] = msg.replace("ASR text:", "[asr]")
    elif "LLM received user message:" in msg:
        record["extra"]["tag_short"] = "USER"
        record["message"] = msg.replace("LLM received user message:", "[user]")
    elif "TTS synthesis OK:" in msg:
        record["extra"]["tag_short"] = "TTS"
        text = msg.replace("TTS synthesis OK:", "").strip()
        if len(text) > 60:
            text = text[:57] + "..."
        record["message"] = f"[tts] {text}"
    elif "Sending first audio segment:" in msg:
        record["extra"]["tag_short"] = "1ST-AUDIO"
        text = msg.replace("Sending first audio segment:", "").strip()
        if len(text) > 50:
            text = text[:47] + "..."
        record["message"] = f"[play] {text}"
    elif "Sending audio message:" in msg:
        return None
    elif "RAG search" in msg or "RAG Inline" in msg:
        record["extra"]["tag_short"] = "RAG"
    elif "LATENCY_E2E" in msg:
        record["extra"]["tag_short"] = "PERF"
        parts_kv = msg.split()
        e2e = tool = tool_name = first = ""
        for p in parts_kv:
            if p.startswith("e2e_ms="):
                e2e = p.split("=")[1]
            elif p.startswith("tool_ms="):
                tool = p.split("=")[1]
            elif p.startswith("tool="):
                tool_name = p.split("=")[1]
            elif p.startswith("first_text="):
                first = p.split("=", 1)[1][:40]
        record["message"] = f"e2e={e2e}ms tool={tool}ms ({tool_name}) > {first}"
    elif "Token usage:" in msg:
        record["extra"]["tag_short"] = "LLM"
    elif "Client disconnected" in msg:
        record["extra"]["tag_short"] = "CONN"
        record["message"] = "disconnected"
    elif "Client connected" in msg:
        record["extra"]["tag_short"] = "CONN"
    elif "Received listen message" in msg or "Received abort message" in msg:
        return None
    elif "Abort message received" in msg:
        return None
    elif "Timeout check task" in msg or "Tool handler cleanup" in msg or "Connection resources" in msg:
        return None

    return record["message"]


def setup_logging():
    check_config_file()
    config = load_config()
    log_config = config["log"]
    global _logger_initialized

    if not _logger_initialized:
        logger.configure(
            extra={
                "selected_module": log_config.get("selected_module", "00000000000000"),
            }
        )

        log_format = log_config.get(
            "log_format",
            "<green>{time:HH:mm:ss}</green> <level>{level: <4}</level> <cyan>{extra[tag_short]: <12}</cyan> <light-green>{message}</light-green>",
        )
        log_format_file = log_config.get(
            "log_format_file",
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <5} | {extra[tag_short]: <12} | {message}",
        )
        log_format = log_format.replace("{version}", SERVER_VERSION)
        log_format_file = log_format_file.replace("{version}", SERVER_VERSION)

        log_level = log_config.get("log_level", "INFO")
        log_dir = log_config.get("log_dir", "tmp")
        log_file = log_config.get("log_file", "server.log")
        data_dir = log_config.get("data_dir", "data")

        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        logger.remove()

        # Console handler
        logger.add(sys.stdout, format=log_format, level=log_level, filter=formatter)

        # File handler (rotation=10MB, retention=30 days, async-safe)
        log_file_path = os.path.join(log_dir, log_file)
        logger.add(
            log_file_path,
            format=log_format_file,
            level=log_level,
            filter=formatter,
            rotation="10 MB",
            retention="30 days",
            compression=None,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        _logger_initialized = True

    return logger


def create_connection_logger(selected_module_str):
    return logger.bind(selected_module=selected_module_str)
