import os
import sys
import uuid
import signal
import asyncio
from dotenv import load_dotenv
load_dotenv()
from aioconsole import ainput
from config.settings import load_config
from config.logger import setup_logging, SERVER_VERSION
from core.utils.util import get_local_ip, validate_mcp_endpoint
from core.http_server import SimpleHttpServer
from core.websocket_server import WebSocketServer
from core.utils.util import check_ffmpeg_installed
from core.utils.gc_manager import get_gc_manager

TAG = __name__
logger = setup_logging()


async def wait_for_exit() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            pass


async def monitor_stdin():
    while True:
        await ainput()


async def main():
    check_ffmpeg_installed()
    config = load_config()

    # Resolve auth_key: config > manager-api secret > random UUID
    auth_key = config["server"].get("auth_key", "")
    if not auth_key or len(auth_key) == 0 or "\u4f60" in auth_key:
        auth_key = config.get("manager-api", {}).get("secret", "")
        if not auth_key or len(auth_key) == 0 or "\u4f60" in auth_key:
            auth_key = str(uuid.uuid4().hex)
    config["server"]["auth_key"] = auth_key

    stdin_task = asyncio.create_task(monitor_stdin())

    gc_manager = get_gc_manager(interval_seconds=300)
    await gc_manager.start()

    # --- RAG warmup ---
    rag_config = dict(config.get("plugins", {}).get("search_from_qdrant", {}))
    if not rag_config:
        logger.bind(tag=TAG).info("RAG warmup skipped: no plugin config")
    else:
        from core.utils.rag_plugin_config import merge_llm_keys_into_rag_config
        rag_config = merge_llm_keys_into_rag_config(rag_config, config)

        provider = rag_config.get("embedding_provider", "gemini")
        if provider in ("local", "fastembed"):
            has_key = True
        elif provider == "bedrock":
            has_key = bool(rag_config.get("bedrock_access_key"))
        elif provider == "gemini":
            has_key = bool(rag_config.get("gemini_api_key"))
        else:
            has_key = bool(rag_config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY"))

        if has_key:
            try:
                from core.utils.rag_manager import rag_manager, inline_rag_manager
                logger.bind(tag=TAG).info("RAG warmup: loading embedding + Qdrant...")
                await rag_manager.warmup(rag_config)
                # Also warmup dedicated inline Qdrant provider (shared across all connections)
                inline_config = dict(rag_config)
                inline_config["rag_provider"] = "qdrant"
                await inline_rag_manager.warmup(inline_config)
            except Exception as e:
                logger.bind(tag=TAG).warning(f"RAG warmup failed (non-fatal): {e}")
        else:
            logger.bind(tag=TAG).info("RAG warmup skipped: no embedding key")

    # --- Start servers ---
    ws_server = WebSocketServer(config)
    ws_task = asyncio.create_task(ws_server.start())
    ota_server = SimpleHttpServer(config)
    ota_task = asyncio.create_task(ota_server.start())

    # --- Print endpoints ---
    ip = get_local_ip()
    http_port = int(config["server"].get("http_port", 8003))
    ws_port = int(config.get("server", {}).get("port", 8000))
    read_config_from_api = config.get("read_config_from_api", False)

    logger.bind(tag=TAG).info("---------------------------------------------")
    logger.bind(tag=TAG).info("Xiaozhi Server v{} started", SERVER_VERSION)
    logger.bind(tag=TAG).info("---------------------------------------------")
    logger.bind(tag=TAG).info("WebSocket   ws://{}:{}/xiaozhi/v1/", ip, ws_port)
    if not read_config_from_api:
        logger.bind(tag=TAG).info("OTA HTTP    http://{}:{}/xiaozhi/ota/", ip, http_port)
    logger.bind(tag=TAG).info("Vision API  http://{}:{}/mcp/vision/explain", ip, http_port)

    mcp_endpoint = config.get("mcp_endpoint", None)
    if mcp_endpoint is not None and "\u4f60" not in mcp_endpoint:
        if validate_mcp_endpoint(mcp_endpoint):
            logger.bind(tag=TAG).info("MCP         {}", mcp_endpoint)
            mcp_endpoint = mcp_endpoint.replace("/mcp/", "/call/")
            config["mcp_endpoint"] = mcp_endpoint
        else:
            logger.bind(tag=TAG).error("MCP endpoint format invalid")
            config["mcp_endpoint"] = "\u4f60\u7684\u63a5\u5165\u70b9 websocket\u5730\u5740"

    logger.bind(tag=TAG).info("---------------------------------------------")

    try:
        await wait_for_exit()
    except asyncio.CancelledError:
        pass
    finally:
        await gc_manager.stop()

        try:
            from core.utils.rag_manager import rag_manager, inline_rag_manager
            if rag_manager.is_initialized:
                await rag_manager.shutdown()
            if inline_rag_manager.is_initialized:
                await inline_rag_manager.shutdown()
        except Exception as e:
            logger.bind(tag=TAG).warning(f"RAG manager shutdown error: {e}")

        stdin_task.cancel()
        ws_task.cancel()
        if ota_task:
            ota_task.cancel()

        await asyncio.wait(
            [stdin_task, ws_task, ota_task] if ota_task else [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        logger.bind(tag=TAG).info("Server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
