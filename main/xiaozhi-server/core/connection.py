import os
import sys
import copy
import json
import uuid
import time
import queue
import random
import asyncio
import threading
import traceback
import subprocess
import websockets

from core.utils.util import (
    extract_json_from_string,
    check_vad_update,
    check_asr_update,
    filter_sensitive_info,
)
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.handle.reportHandle import report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action, ActionResponse
from core.auth import AuthenticationError
from config.config_loader import get_private_config_from_api
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from config.logger import setup_logging, build_module_string, create_connection_logger
from config.manage_api_client import DeviceNotFoundException, DeviceBindException
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from core.utils.util import get_system_error_response
from core.utils import textUtils


TAG = __name__

auto_import_modules("plugins_func.functions")


class TTSException(RuntimeError):
    pass


class ConnectionHandler:
    def __init__(
            self,
            config: Dict[str, Any],
            _vad,
            _asr,
            _llm,
            _memory,
            _intent,
            server=None,
    ):
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        self.logger = setup_logging()
        self.server = server  # 保存server实例的引用

        self.need_bind = False  # 是否需要绑定设备
        self.bind_completed_event = asyncio.Event()
        self.bind_code = None  # 绑定设备的验证码
        self.last_bind_prompt_time = 0  # 上次播放绑定提示的时间戳(秒)
        self.bind_prompt_interval = 60  # 绑定提示播放间隔(秒)

        self.read_config_from_api = self.config.get("read_config_from_api", False)

        self.websocket: websockets.ServerConnection | None = None
        self.headers = None
        self.device_id = None
        self.client_ip = None
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"
        self.sample_rate = 24000  # 默认采样率，从客户端 hello 消息中动态更新

        # 客户端状态相关
        self.client_abort = False
        self.client_is_speaking = False
        self.client_listen_mode = "auto"
        self.agent_orchestrator = None

        # 线程任务相关
        self.loop = None  # 在 handle_connection 中获取运行中的事件循环
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._chat_lock = threading.Lock()  # Prevent parallel chat() calls

        # 添加上报线程池
        self.report_queue = queue.Queue()
        self.report_thread = None
        # 未来可以通过修改此处，调节asr的上报和tts的上报，目前默认都开启
        self.report_asr_enable = self.read_config_from_api
        self.report_tts_enable = self.read_config_from_api

        # 依赖的组件
        self.vad = None
        self.asr = None
        self.tts = None
        self._asr = _asr
        self._vad = _vad
        self.llm = _llm
        self.memory = _memory
        self.memory_long = None
        self.intent = _intent

        # 为每个连接单独管理声纹识别
        self.voiceprint_provider = None

        # TTS echo detection: embedding of the current TTS voice,
        # captured automatically from the first sentence of TTS output.
        self.tts_reference_embedding = None

        # Timestamp (monotonic) when TTS playback last stopped.
        # Used for post-TTS cooldown to let echo dissipate before accepting barge-in.
        self.tts_last_stop_time = 0.0

        # Track recent TTS text segments for ASR echo text filtering.
        # Stores the last N text segments sent to TTS so we can compare
        # ASR transcriptions against them and discard echo.
        self.recent_tts_texts = []
        self._tts_texts_stale = False

        # vad相关变量
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_window = deque(maxlen=5)
        self.first_activity_time = 0.0  # 记录首次活动的时间（毫秒）
        self.last_activity_time = 0.0  # 统一的活动时间戳（毫秒）
        self.client_voice_stop = False
        self.last_is_voice = False

        # asr相关变量
        # 因为实际部署时可能会用到公共的本地ASR，不能把变量暴露给公共ASR
        # 所以涉及到ASR的变量，需要在这里定义，属于connection的私有变量
        self.asr_audio = []
        self.asr_audio_queue = queue.Queue()
        self.current_speaker = None  # 存储当前说话人

        # llm相关变量
        self.dialogue = Dialogue()

        # 工具调用统计（用于监控和自动恢复）
        self.tool_call_stats = {
            'last_call_turn': -1,  # 上次调用工具的轮数
            'consecutive_no_call': 0,  # 连续未调用次数
        }

        # E2E latency metrics (ASR text -> tool -> first audio segment)
        self.latency_trace = {
            'turn_id': None,
            'asr_done_at': 0.0,
            'llm_start_at': 0.0,
            'tool_start_at': 0.0,
            'tool_end_at': 0.0,
            'first_audio_at': 0.0,
            'tool_name': None,
        }
        self.latency_history_ms = deque(maxlen=200)

        # tts相关变量
        self.sentence_id = None
        # 处理TTS响应没有文本返回
        self.tts_MessageText = ""

        # iot相关变量
        self.iot_descriptors = {}
        self.func_handler = None

        self.cmd_exit = self.config["exit_commands"]

        # 是否在聊天结束后关闭连接
        self.close_after_chat = False
        self.load_function_plugin = False
        self.intent_type = "nointent"

        self.timeout_seconds = (
                int(self.config.get("close_connection_no_voice_time", 120)) + 60
        )  # 在原来第一道关闭的基础上加60秒，进行二道关闭
        self.timeout_task = None

        # {"mcp":true} 表示启用MCP功能
        self.features = None

        # 标记连接是否来自MQTT
        self.conn_from_mqtt_gateway = False

        # 初始化提示词管理器
        self.prompt_manager = PromptManager(self.config, self.logger)

        # RAG Inline: Sliding Window state + temporary context
        self._rag_story_state = {
            "story_id": None,
            "doc_id": None,
            "last_part_index": -1,
            "total_parts": 0,
            "sub_offset": 0,
        }
        self._current_rag_context = ""
        self._last_mentioned_stories: list = []
        self._last_suggested_stories: list = []
        self._failed_stories: set = set()

    async def handle_connection(self, ws: websockets.ServerConnection):
        try:
            # 获取运行中的事件循环（必须在异步上下文中）
            self.loop = asyncio.get_running_loop()

            # 获取并验证headers
            self.headers = dict(ws.request.headers)
            real_ip = self.headers.get("x-real-ip") or self.headers.get(
                "x-forwarded-for"
            )
            if real_ip:
                self.client_ip = real_ip.split(",")[0].strip()
            else:
                self.client_ip = ws.remote_address[0]
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - Headers: {self.headers}"
            )

            self.device_id = self.headers.get("device-id", None)

            # 认证通过,继续处理
            self.websocket = ws

            # 检查是否来自MQTT连接
            request_path = ws.request.path
            self.conn_from_mqtt_gateway = request_path.endswith("?from=mqtt_gateway")
            if self.conn_from_mqtt_gateway:
                self.logger.bind(tag=TAG).info("Connection from MQTT gateway")

            # 初始化活动时间戳
            self.first_activity_time = time.time() * 1000
            self.last_activity_time = time.time() * 1000

            # 启动超时检查任务
            self.timeout_task = asyncio.create_task(self._check_timeout())

            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # 从配置中读取采样率
            self.sample_rate = self.welcome_msg["audio_params"]["sample_rate"]
            self.logger.bind(tag=TAG).info(f"Output audio sample rate: {self.sample_rate}")

            # 在后台初始化配置和组件（完全不阻塞主循环）
            asyncio.create_task(self._background_initialize())

            try:
                async for message in self.websocket:
                    await self._route_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.bind(tag=TAG).info("Client disconnected")

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(f"Connection error: {str(e)}-{stack_trace}")
            return
        finally:
            try:
                await self._save_and_close(ws)
            except Exception as final_error:
                self.logger.bind(tag=TAG).error(f"Error during final cleanup: {final_error}")
                # 确保即使保存记忆失败，也要关闭连接
                try:
                    await self.close(ws)
                except Exception as close_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error forcing connection close: {close_error}"
                    )

    async def _save_and_close(self, ws):
        """保存记忆并关闭连接"""
        try:
            if self.memory:
                # 使用线程池异步保存记忆
                def save_memory_task():
                    try:
                        # 创建新事件循环（避免与主循环冲突）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(
                                self.dialogue.dialogue, self.session_id
                            )
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"Failed to save memory: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                # 启动线程保存记忆，不等待完成
                threading.Thread(target=save_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to save memory: {e}")

        # Long-term memory save (Mem0 + Qdrant) in parallel
        try:
            if self.memory_long:
                def save_long_memory_task():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory_long.save_memory(
                                self.dialogue.dialogue, self.session_id
                            )
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(
                            f"Failed to save long-term memory: {e}"
                        )
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                threading.Thread(target=save_long_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to save long-term memory: {e}")

        finally:
            # 立即关闭连接，不等待记忆保存完成
            try:
                await self.close(ws)
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"Failed to close connection after saving memory: {close_error}"
                )

    async def _discard_message_with_bind_prompt(self):
        """丢弃消息并检查是否需要播放绑定提示"""
        if not self.need_bind:
            return
        current_time = time.time()
        if current_time - self.last_bind_prompt_time >= self.bind_prompt_interval:
            self.last_bind_prompt_time = current_time
            from core.handle.receiveAudioHandle import check_bind_device
            asyncio.create_task(check_bind_device(self))

    async def _route_message(self, message):
        """消息路由"""
        # MCP và hello messages phải đi qua ngay — không chờ gate
        if isinstance(message, str):
            try:
                msg_data = json.loads(message)
                msg_type = msg_data.get("type", "")
                if msg_type in ("hello", "mcp"):
                    await handleTextMessage(self, message)
                    return
            except (json.JSONDecodeError, TypeError):
                pass

        # Audio và text messages khác — chờ gate mở
        if not self.bind_completed_event.is_set():
            try:
                await asyncio.wait_for(self.bind_completed_event.wait(), timeout=1)
            except asyncio.TimeoutError:
                await self._discard_message_with_bind_prompt()
                return

        if self.need_bind:
            await self._discard_message_with_bind_prompt()
            return

        if isinstance(message, str):
            await handleTextMessage(self, message)
        elif isinstance(message, bytes):
            if self.vad is None or self.asr is None:
                return

            # 处理来自MQTT网关的音频包
            if self.conn_from_mqtt_gateway and len(message) >= 16:
                handled = await self._process_mqtt_audio_message(message)
                if handled:
                    return

            # 不需要头部处理或没有头部时，直接处理原始消息
            self.asr_audio_queue.put(message)

    async def _process_mqtt_audio_message(self, message):
        """
        处理来自MQTT网关的音频消息，解析16字节头部并提取音频数据

        Args:
            message: 包含头部的音频消息

        Returns:
            bool: 是否成功处理了消息
        """
        try:
            # 提取头部信息
            timestamp = int.from_bytes(message[8:12], "big")
            audio_length = int.from_bytes(message[12:16], "big")

            # 提取音频数据
            if audio_length > 0 and len(message) >= 16 + audio_length:
                # 有指定长度，提取精确的音频数据
                audio_data = message[16 : 16 + audio_length]
                # 基于时间戳进行排序处理
                self._process_websocket_audio(audio_data, timestamp)
                return True
            elif len(message) > 16:
                # 没有指定长度或长度无效，去掉头部后处理剩余数据
                audio_data = message[16:]
                self.asr_audio_queue.put(audio_data)
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to parse WebSocket audio packet: {e}")

        # 处理失败，返回False表示需要继续处理
        return False

    def _process_websocket_audio(self, audio_data, timestamp):
        """处理WebSocket格式的音频包"""
        # 初始化时间戳序列管理
        if not hasattr(self, "audio_timestamp_buffer"):
            self.audio_timestamp_buffer = {}
            self.last_processed_timestamp = 0
            self.max_timestamp_buffer_size = 20

        # 如果时间戳是递增的，直接处理
        if timestamp >= self.last_processed_timestamp:
            self.asr_audio_queue.put(audio_data)
            self.last_processed_timestamp = timestamp

            # 处理缓冲区中的后续包
            processed_any = True
            while processed_any:
                processed_any = False
                for ts in sorted(self.audio_timestamp_buffer.keys()):
                    if ts > self.last_processed_timestamp:
                        buffered_audio = self.audio_timestamp_buffer.pop(ts)
                        self.asr_audio_queue.put(buffered_audio)
                        self.last_processed_timestamp = ts
                        processed_any = True
                        break
        else:
            # 乱序包，暂存
            if len(self.audio_timestamp_buffer) < self.max_timestamp_buffer_size:
                self.audio_timestamp_buffer[timestamp] = audio_data
            else:
                self.asr_audio_queue.put(audio_data)

    async def handle_restart(self, _message):
        """处理服务器重启请求"""
        try:

            self.logger.bind(tag=TAG).info("Server restart command received, preparing...")

            # 发送确认响应
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "服务器重启中...",
                        "content": {"action": "restart"},
                    }
                )
            )

            # 异步执行重启操作
            def restart_server():
                """实际执行重启的方法"""
                time.sleep(1)
                self.logger.bind(tag=TAG).info("Executing server restart...")
                subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    start_new_session=True,
                )
                os._exit(0)

            # 使用线程执行重启避免阻塞事件循环
            threading.Thread(target=restart_server, daemon=True).start()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Restart failed: {str(e)}")
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"Restart failed: {str(e)}",
                        "content": {"action": "restart"},
                    }
                )
            )

    def _initialize_components(self):
        try:
            if self.tts is None:
                self.tts = self._initialize_tts()
            # 打开语音合成通道
            asyncio.run_coroutine_threadsafe(
                self.tts.open_audio_channels(self), self.loop
            )

            # Phát "Đang cấu hình..." ngay sau khi TTS sẵn sàng
            if not self.need_bind:
                try:
                    from core.handle.sendAudioHandle import sendAudio, send_tts_message
                    from core.utils.util import audio_to_data
                    import time as _time
                    _time.sleep(0.3)
                    fut = asyncio.run_coroutine_threadsafe(self._play_loading_sound(), self.loop)
                    fut.result(timeout=5)
                except Exception as e:
                    self.logger.bind(tag=TAG).debug(f"Loading sound skipped: {e}")

            if self.need_bind:
                self.bind_completed_event.set()
                return
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            """初始化组件"""
            if self.config.get("prompt") is not None:
                user_prompt = self.config["prompt"]
                # 使用快速提示词进行初始化
                prompt = self.prompt_manager.get_quick_prompt(user_prompt)
                self.change_system_prompt(prompt)
                self.logger.bind(tag=TAG).info(
                    f"Quick init: prompt OK (first 50 chars): {prompt[:50]}..."
                )

            """初始化本地组件"""
            if self.vad is None:
                self.vad = self._vad
            if self.asr is None:
                self.asr = self._initialize_asr()

            """Khởi tạo Agent Runtime (chỉ cần VAD)"""
            self.agent_orchestrator = None
            try:
                import os
                if os.environ.get("USE_AGENT_RUNTIME", "1") == "1":
                    from core.agent.runtime.orchestrator import AgentOrchestrator
                    self.agent_orchestrator = AgentOrchestrator(self.vad)
                    self.logger.bind(tag=TAG).info("Agent Runtime initialized")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Failed to initialize Agent Runtime: {e}")
                self.agent_orchestrator = None

            # 初始化声纹识别
            self._initialize_voiceprint()
            # 打开语音识别通道
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )

            """加载记忆"""
            self._initialize_memory()
            """加载意图识别"""
            self._initialize_intent()
            """初始化上报线程"""
            self._init_report_threads()
            """更新系统提示词"""
            self._init_prompt_enhancement()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to instantiate components: {e}")

    def _init_prompt_enhancement(self):

        # 更新上下文信息
        self.prompt_manager.update_context_info(self, self.client_ip)
        enhanced_prompt = self.prompt_manager.build_enhanced_prompt(
            self.config["prompt"], self.device_id, self.client_ip
        )
        if enhanced_prompt:
            self.change_system_prompt(enhanced_prompt)
            self.logger.bind(tag=TAG).debug("System prompt enhanced and updated")

    def _init_report_threads(self):
        """初始化ASR和TTS上报线程"""
        if not self.read_config_from_api or self.need_bind:
            return
        if self.chat_history_conf == 0:
            return
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info("TTS report thread started")

    def _initialize_tts(self):
        """初始化TTS"""
        tts = None
        if not self.need_bind:
            tts = initialize_tts(self.config)

        if tts is None:
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts

    def _initialize_asr(self):
        """初始化ASR"""
        if (
                self._asr is not None
                and hasattr(self._asr, "interface_type")
                and self._asr.interface_type == InterfaceType.LOCAL
        ):
            # 如果公共ASR是本地服务，则直接返回
            # 因为本地一个实例ASR，可以被多个连接共享
            asr = self._asr
        else:
            # 如果公共ASR是远程服务，则初始化一个新实例
            # 因为远程ASR，涉及到websocket连接和接收线程，需要每个连接一个实例
            asr = initialize_asr(self.config)

        return asr

    def _initialize_voiceprint(self):
        """Init voiceprint recognition for TTS echo detection."""
        try:
            voiceprint_config = self.config.get("voiceprint", {})
            if not voiceprint_config or not voiceprint_config.get("url"):
                self.logger.bind(tag=TAG).info("Voiceprint not configured — skipping")
                return

            voiceprint_provider = VoiceprintProvider(voiceprint_config)
            if voiceprint_provider is None or not voiceprint_provider.enabled:
                self.logger.bind(tag=TAG).warning(
                    "Voiceprint server unavailable — TTS echo detection disabled"
                )
                return

            self.voiceprint_provider = voiceprint_provider
            self.logger.bind(tag=TAG).info(
                "Voiceprint enabled for TTS echo detection"
            )
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"Voiceprint initialization failed: {str(e)}")

    async def _play_loading_sound(self):
        """Phát âm thanh 'Đang cấu hình...' khi bắt đầu init."""
        from core.handle.sendAudioHandle import sendAudio, send_tts_message
        from core.utils.util import audio_to_data
        await send_tts_message(self, "start")
        await send_tts_message(self, "sentence_start", text="Đang cấu hình dữ liệu...")
        audios = await audio_to_data("config/assets/setup_loading.mp3", is_opus=True)
        await sendAudio(self, audios)

    async def _background_initialize(self):
        """在后台初始化配置和组件（完全不阻塞主循环）"""
        try:
            await self._initialize_private_config_async()

            if self.executor:
                future = self.loop.run_in_executor(None, self._initialize_components)
                await future

            # Phát "Đã sẵn sàng" + mở gate cho user
            if self.tts and not self.need_bind:
                try:
                    from core.handle.sendAudioHandle import sendAudio, _wait_for_audio_completion, send_tts_message
                    from core.utils.util import audio_to_data
                    await send_tts_message(self, "start")
                    await send_tts_message(self, "sentence_start", text="Đã sẵn sàng!")
                    audios = await audio_to_data("config/assets/setup_complete.mp3", is_opus=True)
                    await sendAudio(self, audios)
                    await _wait_for_audio_completion(self)
                    # Gửi stop trực tiếp — không qua send_tts_message (tránh audio_rate_controller crash)
                    await self.websocket.send(json.dumps({
                        "type": "tts", "state": "stop", "session_id": self.session_id
                    }))
                    self.client_is_speaking = False
                except Exception as e:
                    self.logger.bind(tag=TAG).debug(f"Setup complete sound skipped: {e}")

            # MỞ GATE — cho phép user tương tác SAU KHI mọi thứ sẵn sàng
            if not self.need_bind:
                self.bind_completed_event.set()
                self.logger.bind(tag=TAG).info("All components ready — accepting user input")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Background initialization failed: {e}")
            self.bind_completed_event.set()

    async def _initialize_private_config_async(self):
        """从接口异步获取差异化配置（异步版本，不阻塞主循环）"""
        if not self.read_config_from_api:
            self.need_bind = False
            return
        try:
            begin_time = time.time()
            private_config = await get_private_config_from_api(
                self.config,
                self.headers.get("device-id"),
                self.headers.get("client-id", self.headers.get("device-id")),
            )
            private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
            self.logger.bind(tag=TAG).info(
                f"{time.time() - begin_time:.3f}s async private config fetch OK: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}"
            )
            self.need_bind = False
        except DeviceNotFoundException as e:
            self.need_bind = True
            private_config = {}
        except DeviceBindException as e:
            self.need_bind = True
            self.bind_code = e.bind_code
            private_config = {}
        except Exception as e:
            self.need_bind = True
            self.logger.bind(tag=TAG).error(f"Async private config fetch failed: {e}")
            private_config = {}

        init_llm, init_tts, init_memory, init_intent = (
            False,
            False,
            False,
            False,
        )

        init_vad = check_vad_update(self.common_config, private_config)
        init_asr = check_asr_update(self.common_config, private_config)

        if init_vad:
            self.config["VAD"] = private_config["VAD"]
            self.config["selected_module"]["VAD"] = private_config["selected_module"][
                "VAD"
            ]
        if init_asr:
            self.config["ASR"] = private_config["ASR"]
            self.config["selected_module"]["ASR"] = private_config["selected_module"][
                "ASR"
            ]
        if private_config.get("TTS", None) is not None:
            init_tts = True
            self.config["TTS"] = private_config["TTS"]
            self.config["selected_module"]["TTS"] = private_config["selected_module"][
                "TTS"
            ]
        if private_config.get("LLM", None) is not None:
            init_llm = True
            self.config["LLM"] = private_config["LLM"]
            self.config["selected_module"]["LLM"] = private_config["selected_module"][
                "LLM"
            ]
        if private_config.get("VLLM", None) is not None:
            self.config["VLLM"] = private_config["VLLM"]
            self.config["selected_module"]["VLLM"] = private_config["selected_module"][
                "VLLM"
            ]
        if private_config.get("Memory", None) is not None:
            init_memory = True
            self.config["Memory"] = private_config["Memory"]
            self.config["selected_module"]["Memory"] = private_config[
                "selected_module"
            ]["Memory"]
        if private_config.get("Intent", None) is not None:
            init_intent = True
            self.config["Intent"] = private_config["Intent"]
            model_intent = private_config.get("selected_module", {}).get("Intent", {})
            self.config["selected_module"]["Intent"] = model_intent
            # 加载插件配置
            if model_intent != "Intent_nointent":
                plugin_from_server = private_config.get("plugins", {})
                for plugin, config_str in plugin_from_server.items():
                    plugin_from_server[plugin] = json.loads(config_str)
                # Preserve local RAG plugin (search_from_qdrant) — API doesn't manage it
                existing_qdrant = self.config.get("plugins", {}).get("search_from_qdrant")
                self.config["plugins"] = plugin_from_server
                if existing_qdrant and "search_from_qdrant" not in plugin_from_server:
                    self.config["plugins"]["search_from_qdrant"] = existing_qdrant
                self.config["Intent"][self.config["selected_module"]["Intent"]][
                    "functions"
                ] = list(plugin_from_server.keys())
        if private_config.get("prompt", None) is not None:
            if self.config.get("prompt"):
                self.logger.bind(tag=TAG).info(
                    "Keeping local prompt (ignoring API prompt)"
                )
            else:
                self.config["prompt"] = private_config["prompt"]
        # 获取声纹信息
        if private_config.get("voiceprint", None) is not None:
            self.config["voiceprint"] = private_config["voiceprint"]
        if private_config.get("summaryMemory", None) is not None:
            self.config["summaryMemory"] = private_config["summaryMemory"]
        if private_config.get("device_max_output_size", None) is not None:
            self.max_output_size = int(private_config["device_max_output_size"])
        if private_config.get("chat_history_conf", None) is not None:
            self.chat_history_conf = int(private_config["chat_history_conf"])
        if private_config.get("mcp_endpoint", None) is not None:
            self.config["mcp_endpoint"] = private_config["mcp_endpoint"]
        if private_config.get("context_providers", None) is not None:
            self.config["context_providers"] = private_config["context_providers"]

        need_reinit = init_vad or init_asr
        if need_reinit:
            try:
                if self.tts is None:
                    self.tts = self._initialize_tts()

                from core.handle.sendAudioHandle import sendAudio, _wait_for_audio_completion, send_tts_message
                from core.utils.util import audio_to_data
                self.logger.bind(tag=TAG).info("Hot-swap starting: Sending pre-recorded loading audio")

                await send_tts_message(self, "start")
                await send_tts_message(self, "sentence_start", text="Đang cấu hình dữ liệu...")

                audios = await audio_to_data("config/assets/setup_loading.mp3", is_opus=True)
                await sendAudio(self, audios)
                await _wait_for_audio_completion(self)

            except Exception as e:
                self.logger.bind(tag=TAG).warning(f"Failed to send loading indicator: {e}")

        # 使用 run_in_executor 在线程池中执行 initialize_modules，避免阻塞主循环
        try:
            modules = await self.loop.run_in_executor(
                None,  # 使用默认线程池
                initialize_modules,
                self.logger,
                private_config,
                init_vad,
                init_asr,
                init_llm,
                init_tts,
                init_memory,
                init_intent,
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to initialize modules: {e}")
            modules = {}

        if need_reinit:
            try:
                if modules.get("asr"):
                    self.server._asr = modules["asr"]
                if modules.get("vad"):
                    self.server._vad = modules["vad"]
                self.server.config = self.config
                
                self.logger.bind(tag=TAG).info("Hot-swap complete: Sending pre-recorded completion audio.")
                
                from core.handle.sendAudioHandle import sendAudio, _wait_for_audio_completion, send_tts_message
                from core.utils.util import audio_to_data
                await send_tts_message(self, "start")
                await send_tts_message(self, "sentence_start", text="Đã cấu hình xong rồi, hãy bấm lại nha!")

                audios = await audio_to_data("config/assets/setup_complete.mp3", is_opus=True)
                await sendAudio(self, audios)
                await _wait_for_audio_completion(self)
                
                if not self.stop_event.is_set():
                    self.stop_event.set()
                await self.close(self.websocket)
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Failed to sync state or send finish indicator: {e}")
            return

        if modules.get("tts", None) is not None:
            self.tts = modules["tts"]
        if modules.get("vad", None) is not None:
            self.vad = modules["vad"]
        if modules.get("asr", None) is not None:
            self.asr = modules["asr"]
        if modules.get("llm", None) is not None:
            self.llm = modules["llm"]
        if modules.get("intent", None) is not None:
            self.intent = modules["intent"]
        if modules.get("memory", None) is not None:
            self.memory = modules["memory"]

        # RAG: warmup sau khi đã merge plugin từ manager-api (startup warmup dùng config chưa có agent → lần đầu search bị cold + timeout 120s)
        try:
            await self._warmup_rag_plugin_async()
        except Exception as e:
            self.logger.bind(tag=TAG).warning(
                f"RAG warmup after agent config failed (non-fatal): {e}"
            )

    async def _warmup_rag_plugin_async(self):
        """Pre-load embedding + Qdrant với cùng merge key như search_from_qdrant."""
        from core.utils.rag_plugin_config import merge_llm_keys_into_rag_config
        from core.utils.rag_manager import inline_rag_manager
        from core.utils.story_registry import story_registry

        base = dict(self.config.get("plugins", {}).get("search_from_qdrant") or {})
        if not base:
            return
        rag = merge_llm_keys_into_rag_config(base, self.config)
        rag["rag_provider"] = "qdrant"
        provider = rag.get("embedding_provider", "gemini")
        if provider == "gemini":
            has_key = bool(rag.get("gemini_api_key"))
        else:
            has_key = bool(rag.get("openai_api_key") or os.environ.get("OPENAI_API_KEY"))
        if not has_key:
            return
        if not inline_rag_manager.will_recreate_provider(rag):
            return
        self.logger.bind(tag=TAG).info(
            "RAG warmup: agent config (embedding + Qdrant, avoid cold first search)..."
        )
        await inline_rag_manager.warmup(rag)

        # Build dynamic story registry from Qdrant (once, shared across connections)
        if not story_registry.is_built:
            try:
                rag_provider = inline_rag_manager.get_provider(rag)
                if hasattr(rag_provider, "list_unique_stories"):
                    count = await story_registry.build(rag_provider)
                    self.logger.bind(tag=TAG).info(
                        f"StoryRegistry built at warmup: {count} stories"
                    )
            except Exception as e:
                self.logger.bind(tag=TAG).warning(
                    f"StoryRegistry build failed (non-fatal): {e}"
                )

    def _initialize_memory(self):
        if self.memory is None:
            return
        """初始化记忆模块"""
        self.memory.init_memory(
            role_id=self.device_id,
            llm=self.llm,
            summary_memory=self.config.get("summaryMemory", None),
            save_to_file=True,
        )

        # 获取记忆总结配置
        memory_config = self.config.get("Memory", {})
        selected_memory = self.config.get("selected_module", {}).get("Memory")
        if not selected_memory or selected_memory not in memory_config:
            return
        memory_type = memory_config[selected_memory].get("type", "nomem")
        # 如果使用 nomem，直接返回
        if memory_type == "nomem":
            return
        # 使用 mem_local_short 模式
        elif memory_type == "mem_local_short":
            memory_llm_name = memory_config[selected_memory].get(
                "llm"
            )
            if memory_llm_name and memory_llm_name in self.config.get("LLM", {}):
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                memory_llm_config = self.config["LLM"][memory_llm_name]
                memory_llm_type = memory_llm_config.get("type", memory_llm_name)
                memory_llm = llm_utils.create_instance(
                    memory_llm_type, memory_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Created dedicated LLM for memory summary: {memory_llm_name}, type: {memory_llm_type}"
                )
                self.memory.set_llm(memory_llm)
            else:
                # 否则使用主LLM
                self.memory.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Using main LLM for memory summary")

        # Long-term memory (Mem0 OSS + Qdrant)
        lt_cfg = self.config.get("long_term_memory", {})
        self.logger.bind(tag=TAG).info(f"Long-term memory config: {lt_cfg}")
        if lt_cfg.get("enabled"):
            try:
                provider_name = lt_cfg["provider"]
                lt_config = dict(self.config["Memory"][provider_name])

                # Inject OpenAI API key from active LLM config into embedder
                embedder_cfg = lt_config.get("embedder", {})
                llm_module = self.config["selected_module"]["LLM"]
                llm_conf = self.config["LLM"][llm_module]
                llm_key = llm_conf.get("api_key", "")

                if embedder_cfg.get("provider") == "openai":
                    embed_inner = dict(embedder_cfg.get("config", {}))
                    if not embed_inner.get("api_key") and llm_key:
                        embed_inner["api_key"] = llm_key
                        lt_config["embedder"] = {
                            "provider": "openai",
                            "config": embed_inner,
                        }
                        self.logger.bind(tag=TAG).info(
                            "Injected OpenAI API key from LLM into mem0 embedder"
                        )

                # Inject LLM config for mem0 fact extraction (if not explicitly set)
                if not lt_config.get("llm") and llm_key:
                    lt_config["llm"] = {
                        "provider": "openai",
                        "config": {
                            "model": llm_conf.get("model_name", "gpt-4o-mini"),
                            "api_key": llm_key,
                        },
                    }
                    base_url = llm_conf.get("base_url")
                    if base_url:
                        lt_config["llm"]["config"]["openai_base_url"] = base_url

                from core.utils import memory as memory_utils
                self.memory_long = memory_utils.create_instance(
                    lt_config["type"], lt_config, None
                )

                if not getattr(self.memory_long, "use_mem0", False):
                    self.logger.bind(tag=TAG).error(
                        "Long-term memory provider created but Mem0 client init failed"
                    )
                    self.memory_long = None
                else:
                    self.memory_long.init_memory(role_id=self.device_id, llm=self.llm)
                    self.logger.bind(tag=TAG).info(
                        f"Long-term memory initialized: {provider_name}"
                    )
            except Exception as e:
                self.logger.bind(tag=TAG).error(
                    f"Failed to init long-term memory: {e}"
                )
                self.memory_long = None

    def _initialize_intent(self):
        if self.intent is None:
            return
        self.intent_type = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ]["type"]
        if self.intent_type == "function_call" or self.intent_type == "intent_llm":
            self.load_function_plugin = True
        """初始化意图识别模块"""
        # 获取意图识别配置
        intent_config = self.config["Intent"]
        intent_type = self.config["Intent"][self.config["selected_module"]["Intent"]][
            "type"
        ]

        # 如果使用 nointent，直接返回
        if intent_type == "nointent":
            return
        # 使用 intent_llm 模式
        elif intent_type == "intent_llm":
            intent_llm_name = intent_config[self.config["selected_module"]["Intent"]][
                "llm"
            ]

            if intent_llm_name and intent_llm_name in self.config["LLM"]:
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                intent_llm_config = self.config["LLM"][intent_llm_name]
                intent_llm_type = intent_llm_config.get("type", intent_llm_name)
                intent_llm = llm_utils.create_instance(
                    intent_llm_type, intent_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Created dedicated LLM for intent recognition: {intent_llm_name}, type: {intent_llm_type}"
                )
                self.intent.set_llm(intent_llm)
            else:
                # 否则使用主LLM
                self.intent.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Using main LLM for intent recognition")

        """加载统一工具处理器"""
        self.func_handler = UnifiedToolHandler(self)

        # 异步初始化工具处理器
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(self.func_handler._initialize(), self.loop)

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # 更新系统prompt至上下文
        self.dialogue.update_system_message(self.prompt)

    def mark_latency_asr_done(self, query: str | None = None):
        now = time.perf_counter()
        self.latency_trace = {
            'turn_id': str(uuid.uuid4()),
            'asr_done_at': now,
            'llm_start_at': 0.0,
            'tool_start_at': 0.0,
            'tool_end_at': 0.0,
            'first_audio_at': 0.0,
            'tool_name': None,
        }
        if query:
            self.logger.bind(tag=TAG).debug(
                f"LATENCY trace start turn={self.latency_trace['turn_id']} query={query[:80]}"
            )

    def mark_latency_tool_start(self, tool_name: str):
        if self.latency_trace.get('asr_done_at', 0.0) <= 0:
            return
        self.latency_trace['tool_start_at'] = time.perf_counter()
        self.latency_trace['tool_name'] = tool_name

    def mark_latency_tool_end(self):
        if self.latency_trace.get('asr_done_at', 0.0) <= 0:
            return
        self.latency_trace['tool_end_at'] = time.perf_counter()

    def mark_latency_first_audio(self, text: str | None = None):
        if self.latency_trace.get('asr_done_at', 0.0) <= 0:
            return
        if self.latency_trace.get('first_audio_at', 0.0) > 0:
            return
        now = time.perf_counter()
        self.latency_trace['first_audio_at'] = now

        asr_done = self.latency_trace.get('asr_done_at', 0.0)
        llm_start = self.latency_trace.get('llm_start_at', 0.0)
        tool_start = self.latency_trace.get('tool_start_at', 0.0)
        tool_end = self.latency_trace.get('tool_end_at', 0.0)

        e2e_ms = (now - asr_done) * 1000.0 if asr_done > 0 else 0.0
        llm_ms = (llm_start - asr_done) * 1000.0 if llm_start > 0 and asr_done > 0 else 0.0
        tool_ms = (tool_end - tool_start) * 1000.0 if tool_end > 0 and tool_start > 0 else 0.0

        self.latency_history_ms.append(e2e_ms)
        sorted_vals = sorted(self.latency_history_ms)
        n = len(sorted_vals)
        def _pct(p):
            if n == 0:
                return 0.0
            if n == 1:
                return float(sorted_vals[0])
            rank = (p / 100.0) * (n - 1)
            lo = int(rank)
            hi = min(lo + 1, n - 1)
            frac = rank - lo
            return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)

        p50 = _pct(50)
        p95 = _pct(95)

        self.logger.bind(tag=TAG).info(
            "LATENCY_E2E "
            f"turn={self.latency_trace.get('turn_id')} "
            f"e2e_ms={e2e_ms:.1f} "
            f"llm_queue_ms={llm_ms:.1f} "
            f"tool_ms={tool_ms:.1f} "
            f"tool={self.latency_trace.get('tool_name') or '-'} "
            f"p50_ms={p50:.1f} p95_ms={p95:.1f} n={n} "
            f"first_text={(text or '')[:40]}"
        )

    def chat(self, query, depth=0):
        # Prevent parallel chat() calls from overlapping LLM streams
        if depth == 0:
            if not self._chat_lock.acquire(blocking=False):
                self.logger.bind(tag=TAG).warning(
                    f"[CHAT_GUARD] Dropping duplicate chat() call: {(query or '')[:60]}"
                )
                return None

        try:
            return self._chat_inner(query, depth)
        finally:
            if depth == 0:
                self._chat_lock.release()

    def _chat_inner(self, query, depth=0):
        if query is not None:
            if depth == 0:
                self._recent_tool_calls = set()
                self.mark_latency_asr_done(query)
                self.latency_trace['llm_start_at'] = time.perf_counter()

                # Second-layer echo guard: if the raw text content is suspiciously
                # long (>100 chars), it is almost certainly TTS echo that slipped
                # past the ASR filter.  Drop it to keep the dialogue clean.
                try:
                    parsed = json.loads(query)
                    raw_content = parsed.get("content", "")
                except (json.JSONDecodeError, TypeError, AttributeError):
                    raw_content = query
                if len(raw_content) > 100:
                    self.logger.bind(tag=TAG).warning(
                        f"[ECHO_GUARD] Dropping likely echo in chat() "
                        f"({len(raw_content)} chars): {raw_content[:60]}..."
                    )
                    return None

            self.logger.bind(tag=TAG).info(f"LLM received user message: {query}")

        # [RAG Inline - Mode B] Inject context từ Qdrant vào query trước khi gọi LLM
        # Chỉ áp dụng ở depth=0 (lượt đầu tiên) và khi có query thực sự
        if query is not None and depth == 0:
            # Extract plain text from JSON ASR output for RAG search.
            # ASR sends {"speaker": "...", "content": "...", "confidence": 0.x}
            # but RAG embedding must only receive the actual user utterance.
            try:
                _parsed_q = json.loads(query)
                rag_query = _parsed_q.get("content", "").strip() if isinstance(_parsed_q, dict) else query
            except (json.JSONDecodeError, TypeError, AttributeError):
                rag_query = query
            rag_query = rag_query or query

            rag_inline_context = self._get_inline_rag_context(rag_query)
            if rag_inline_context:
                self._current_rag_context = rag_inline_context
                self.logger.bind(tag=TAG).info(
                    f"RAG Inline: context stored ({len(rag_inline_context)} chars), "
                    f"will inject before LLM call"
                )
            else:
                self._current_rag_context = ""
                # Guard: no RAG context → use intent-based guard messages
                # (guards are already injected by _classify_intent via dialogue.put)
                # Only add fallback guard if no intent-based guard was injected
                stripped_q = rag_query.strip()
                if len(stripped_q) <= 3:
                    self.dialogue.put(
                        Message(
                            role="system",
                            content="[Lưu ý] Câu nói của bé rất ngắn/không rõ nghĩa. "
                                    "KHÔNG tự bịa truyện. Hỏi lại bé nhẹ nhàng.",
                            is_temporary=True,
                        )
                    )

        # 为最顶层时新建会话ID和发送FIRST请求
        if depth == 0:
            self.sentence_id = str(uuid.uuid4().hex)
            self.dialogue.put(Message(role="user", content=query))
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
            
            # Send an immediate quick filler only when RAG is active (slower path)
            _rag_ctx = getattr(self, "_current_rag_context", "")
            if _rag_ctx:
                try:
                    story_fillers = [
                        "Chờ cô nhớ lại xíu nha. ",
                        "Đợi cô xíu nè. ",
                        "Ừm, để cô nhớ lại nha. ",
                        "Chờ cô xíu nha. ",
                        "Để cô kể bé nha. ",
                    ]
                    filler = random.choice(story_fillers)
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=filler,
                        )
                    )
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Quick filler TTS error: {e}")


        # 设置最大递归深度，避免无限循环，可根据实际需求调整
        MAX_DEPTH = 3
        force_final_answer = False  # 标记是否强制最终回答

        if depth >= MAX_DEPTH:
            self.logger.bind(tag=TAG).debug(
                f"Max tool-call depth {MAX_DEPTH} reached; forcing answer from existing context"
            )
            force_final_answer = True
            self.dialogue.put(
                Message(
                    role="user",
                    content="[系统提示] 已达到最大工具调用次数限制，请你基于目前已经获取的所有信息，直接给出最终答案。不要再尝试调用任何工具。",
                )
            )

        # 长对话工具调用提醒：当对话轮数较多时，提醒模型正确使用工具
        force_reminder = False  # 是否强制提醒

        if depth == 0 and query is not None:
            dialogue_length = len(self.dialogue.dialogue)
            current_turn = dialogue_length // 2

            # 检测距离上一次连续未调用工具的情况
            if self.tool_call_stats['last_call_turn'] >= 0:
                turns_since_last = current_turn - self.tool_call_stats['last_call_turn']
                if turns_since_last > 3:  # 超过3轮未调用
                    self.logger.bind(tag=TAG).warning(
                        f"No tool calls for {turns_since_last} turn(s); possible lazy-reply mode, injecting reminder"
                    )
                    force_reminder = True

            max_dialogue_turns = 5
            if dialogue_length > max_dialogue_turns * 2:
                removed = self.dialogue.trim_history(max_turns=max_dialogue_turns)
                if removed > 0:
                    self.logger.bind(tag=TAG).info(
                        f"Dialogue too long ({dialogue_length} msgs), trimmed to last {max_dialogue_turns} turns, removed {removed} msgs"
                    )

        # Define intent functions
        functions = None
        # 达到最大深度时，禁用工具调用，强制 LLM 直接回答
        if (
                self.intent_type == "function_call"
                and hasattr(self, "func_handler")
                and not force_final_answer
                and not self.config.get("disable_tools", False)
        ):
            functions = self.func_handler.get_functions()

        # Tool-call force escalation (only for non-RAG tools like weather, music)
        tool_call_reminder = None
        if depth == 0 and query is not None and functions is not None and force_reminder:
            tool_summary = self._get_tool_summary(functions)
            if tool_summary:
                tool_call_reminder = (
                    f"[Nhắc nhở] Công cụ hiện có: {tool_summary}. Kiểm tra lại có cần gọi không."
                )

        # Ràng buộc phản hồi giọng nói: ưu tiên time-to-first-audio < 3s.
        concise_voice_reminder = None
        if depth == 0 and query is not None:
            concise_voice_reminder = (
                "[FORMAT] "
                "Mỗi 1-2 câu xuống dòng. Câu dưới 15 từ. Dùng ba chấm tạo pause. "
                "KHÔNG đoạn dài dồn cục. "
                "Gộp cảm thán với câu tiếp, KHÔNG bắt đầu bằng 1 từ rồi xuống dòng. "
                "[LENGTH LIMIT] "
                "Trẻ trả lời → phản hồi TỐI ĐA 3-4 câu (~100 từ), kết bằng 1 câu hỏi mới. "
                "Kể đoạn mới → tối đa 150 từ. KHÔNG kể tiếp quá 100 từ nếu chưa có phản hồi từ trẻ. "
                "Ngắn là vàng. Mỗi lần bot nói chỉ 10-15 giây. "
                "[STORY ARC] "
                "Chuyện chỉ 3-5 đoạn tổng. Theo cốt truyện gốc. "
                "Đoạn cuối: kết trọn vẹn + bài học. KHÔNG cliffhanger đoạn cuối. "
                "Trẻ YÊU CẦU đổi chuyện → đổi ngay. "
                "[KID HANDLING] "
                "Nói sai → KHEN + quay lại cốt truyện. Đổi chuyện → đổi ngay. "
                "KHÔNG BAO GIỜ nói Sai rồi. "
                "[PERFORMANCE] "
                "Diễn như voice actor. Nhập vai nhân vật. SFX tượng thanh. "
                "[CONTINUITY] Phản hồi ĐÚNG ngữ cảnh. KHÔNG lặp lời chào."
            )

        response_message = []

        # Build LLM dialogue with temporary reminders injected directly,
        # WITHOUT storing them in self.dialogue. This guarantees they never
        # pollute the conversation history regardless of aborts or exceptions.
        try:
            # 使用带记忆的对话
            memory_str = None
            # 仅当query非空（代表用户询问）时查询记忆
            if self.memory is not None and query:
                future = asyncio.run_coroutine_threadsafe(
                    self.memory.query_memory(query), self.loop
                )
                memory_str = future.result()
                if memory_str:
                    self.logger.bind(tag=TAG).info(f"Memory injected ({len(memory_str)} chars)")

            # Long-term memory query (Mem0 + Qdrant)
            if self.memory_long is not None and query:
                try:
                    future_lt = asyncio.run_coroutine_threadsafe(
                        self.memory_long.query_memory(query), self.loop
                    )
                    long_str = future_lt.result()
                    if long_str:
                        memory_str = (memory_str or "") + "\n--- Ký ức dài hạn ---\n" + long_str
                        self.logger.bind(tag=TAG).info(
                            f"Long-term memory injected ({len(long_str)} chars)"
                        )
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Long-term memory query error: {e}")

            llm_dialogue = self.dialogue.get_llm_dialogue_with_memory(
                memory_str, self.config.get("voiceprint", {})
            )

            # Inject RAG context into last user message (NOT stored in history)
            _rag_ctx = getattr(self, "_current_rag_context", "")
            if _rag_ctx:
                for i in range(len(llm_dialogue) - 1, -1, -1):
                    if llm_dialogue[i]["role"] == "user":
                        llm_dialogue[i] = dict(llm_dialogue[i])
                        llm_dialogue[i]["content"] = (
                            llm_dialogue[i]["content"] + "\n\n" + _rag_ctx
                        )
                        break
                self._current_rag_context = ""

            # Inject temporary reminders as system messages (NOT user messages)
            # so the LLM treats them as instructions, not as user input.
            if tool_call_reminder:
                llm_dialogue.append({"role": "system", "content": tool_call_reminder})
            if concise_voice_reminder:
                llm_dialogue.append({"role": "system", "content": concise_voice_reminder})

            if self.intent_type == "function_call" and functions is not None:
                # 使用支持functions的streaming接口
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    llm_dialogue,
                    functions=functions,
                )
            else:
                llm_responses = self.llm.response(
                    self.session_id,
                    llm_dialogue,
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM processing error {query}: {e}")
            return None

        # 处理流式响应
        tool_call_flag = False
        # 支持多个并行工具调用 - 使用列表存储
        tool_calls_list = []  # 格式: [{"id": "", "name": "", "arguments": ""}]
        content_arguments = ""
        self.client_abort = False
        emotion_flag = True
        try:
            for response in llm_responses:
                if self.client_abort:
                    break
                if self.intent_type == "function_call" and functions is not None:
                    content, tools_call = response
                    if "content" in response:
                        content = response["content"]
                        tools_call = None
                    if content is not None and len(content) > 0:
                        content_arguments += content

                    if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                        # print("content_arguments", content_arguments)
                        tool_call_flag = True

                    if tools_call is not None and len(tools_call) > 0:
                        tool_call_flag = True
                        self._merge_tool_calls(tool_calls_list, tools_call)
                else:
                    content = response

                # 在llm回复中获取情绪表情，一轮对话只在开头获取一次
                if emotion_flag and content is not None and content.strip():
                    asyncio.run_coroutine_threadsafe(
                        textUtils.get_emotion(self, content),
                        self.loop,
                    )
                    emotion_flag = False

                if content is not None and len(content) > 0:
                    if not tool_call_flag:
                        response_message.append(content)
                        tts_content = content
                        if "[DONE_SENTENCE" in "".join(response_message):
                            import re
                            tts_content = re.sub(
                                r'\[DONE_SENTENCE[:\s\d\]]*$', '', tts_content
                            )
                        if tts_content:
                            self.tts.tts_text_queue.put(
                                TTSMessageDTO(
                                    sentence_id=self.sentence_id,
                                    sentence_type=SentenceType.MIDDLE,
                                    content_type=ContentType.TEXT,
                                    content_detail=tts_content,
                                )
                            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM stream processing error: {e}")
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=get_system_error_response(self.config),
                )
            )
            if depth == 0:
                self.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )
            return

        self.logger.bind(tag=TAG).info(
            f"LLM stream done: tool_call_flag={tool_call_flag}, "
            f"tool_calls={len(tool_calls_list)}, "
            f"content_args_len={len(content_arguments)}, "
            f"response_msgs={len(response_message)}"
        )

        # 处理function call
        if tool_call_flag:
          try:
            bHasError = False

            # Send a thinking filler so user doesn't wait in silence (only on first tool call)
            if (tool_calls_list or content_arguments) and depth == 0:
                try:
                    fillers = ["Ừm. ", "Để cô xem xíu nha. ", "Đợi cô xíu nha. "]
                    filler = random.choice(fillers)
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=filler,
                        )
                    )
                except Exception as filler_err:
                    self.logger.bind(tag=TAG).error(f"Filler TTS error: {filler_err}")

            self.logger.bind(tag=TAG).info(
                f"Tool call processing: tool_calls_list={len(tool_calls_list)}, "
                f"content_arguments={content_arguments[:100] if content_arguments else 'empty'}"
            )

            # 处理基于文本的工具调用格式
            if len(tool_calls_list) == 0 and content_arguments:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        tool_calls_list.append(
                            {
                                "id": str(uuid.uuid4().hex),
                                "name": content_arguments_json["name"],
                                "arguments": json.dumps(
                                    content_arguments_json["arguments"],
                                    ensure_ascii=False,
                                ),
                            }
                        )
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.bind(tag=TAG).error(
                        f"function call error: {content_arguments}"
                    )

            if not bHasError and len(tool_calls_list) > 0:
                # 更新工具调用统计
                if depth == 0:
                    try:
                        current_turn = len(self.dialogue.dialogue) // 2
                        self.tool_call_stats['last_call_turn'] = current_turn
                        self.tool_call_stats['consecutive_no_call'] = 0
                    except Exception as stats_err:
                        self.logger.bind(tag=TAG).error(f"Tool-call stats error: {stats_err}")

                # 如需要大模型先处理一轮，添加相关处理后的日志情况
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.tts_MessageText = text_buff
                    self.dialogue.put(Message(role="assistant", content=text_buff))
                response_message.clear()

                self.logger.bind(tag=TAG).info(
                    f"Detected {len(tool_calls_list)} tool call(s)"
                )

                # 收集所有工具调用的 Future
                futures_with_data = []
                for tool_call_data in tool_calls_list:
                    self.logger.bind(tag=TAG).info(
                        f"function_name={tool_call_data['name']}, function_arguments={tool_call_data['arguments']}"
                    )

                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self.func_handler.handle_llm_function_call(
                                self, tool_call_data
                            ),
                            self.loop,
                        )
                        futures_with_data.append((future, tool_call_data))
                    except Exception as dispatch_err:
                        self.logger.bind(tag=TAG).error(
                            f"Tool dispatch error for {tool_call_data['name']}: {dispatch_err}"
                        )

                # 等待协程结束（实际等待时长为最慢的那个）
                tool_results = []
                for future, tool_call_data in futures_with_data:
                    try:
                        result = future.result(timeout=15)
                    except TimeoutError:
                        self.logger.bind(tag=TAG).warning(
                            f"Tool call timeout (15s): {tool_call_data['name']}"
                        )
                        result = ActionResponse(
                            action=Action.RESPONSE,
                            response=f"Xin lỗi, công cụ {tool_call_data['name']} phản hồi quá lâu. Quý vị thử lại sau nha!",
                        )
                    tool_results.append((result, tool_call_data))

                # 统一处理所有工具调用结果
                if tool_results:
                    self._handle_function_result(tool_results, depth=depth)

          except Exception as tool_err:
            self.logger.bind(tag=TAG).error(f"Tool call block error: {tool_err}", exc_info=True)
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail="Có lỗi khi xử lý, quý vị thử lại nha!",
                )
            )

        # 存储对话内容
        if len(response_message) > 0:
            text_buff = "".join(response_message)

            # Parse [DONE_SENTENCE: N] for anchor point tracking
            import re
            _story_st = getattr(self, "_rag_story_state", None)
            done_match = re.search(r'\[DONE_SENTENCE:\s*(\d+)\]', text_buff)
            if done_match and _story_st and _story_st.get("story_id"):
                done_idx = int(done_match.group(1))
                offsets = _story_st.get("_sentence_offsets", [])
                if offsets and done_idx < len(offsets):
                    _story_st["sub_offset"] = offsets[done_idx]
                elif offsets and done_idx >= len(offsets):
                    _story_st["sub_offset"] = 0
                    _story_st["last_part_index"] = _story_st.get("last_part_index", 0) + 1
                text_buff = re.sub(r'\s*\[DONE_SENTENCE:\s*\d+\]', '', text_buff)
            elif _story_st and _story_st.get("story_id") and _story_st.get("_sentence_offsets"):
                self.logger.bind(tag=TAG).debug(
                    "Anchor point: LLM did not output [DONE_SENTENCE: N], keeping current state"
                )

            self.tts_MessageText = text_buff
            self.dialogue.put(Message(role="assistant", content=text_buff))

            # Track last narrated tail for story continuation context
            if _story_st and _story_st.get("story_id"):
                _story_st["last_narrated_tail"] = text_buff[-200:]

            # 更新工具调用统计：如果没有调用工具，增加计数
            if depth == 0 and not tool_call_flag:
                self.tool_call_stats['consecutive_no_call'] += 1

        # Clean up one-shot instruction messages to free dialogue turns
        if depth == 0:
            self.dialogue.remove_temporary()

        if depth == 0:
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
            # 使用lambda延迟计算，只有在DEBUG级别时才执行get_llm_dialogue()
            self.logger.bind(tag=TAG).debug(
                lambda: json.dumps(
                    self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
                )
            )

        return True

    def _get_tool_summary(self, functions: list) -> str:
        """
        从工具定义中提取摘要，用于规则强化注入

        Args:
            functions: 工具列表

        Returns:
            str: 工具名称字符串
        """
        if not functions:
            return ""

        datas = []
        for func in functions:
            func_info = func.get("function", {})
            name = func_info.get("name", "")
            datas.append(name)
        result = "、".join(datas)
        return result

    def _handle_function_result(self, tool_results, depth):
        need_llm_tools = []

        for result, tool_call_data in tool_results:
            if result.action in [
                Action.RESPONSE,
                Action.NOTFOUND,
                Action.ERROR,
            ]:  # 直接回复前端
                text = result.response if result.response else result.result
                self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
                self.dialogue.put(Message(role="assistant", content=text))
            elif result.action == Action.REQLLM:
                # 收集需要 LLM 处理的工具
                need_llm_tools.append((result, tool_call_data))
            else:
                pass

        if need_llm_tools:
            all_tool_calls = [
                {
                    "id": tool_call_data["id"],
                    "function": {
                        "arguments": (
                            "{}"
                            if tool_call_data["arguments"] == ""
                            else tool_call_data["arguments"]
                        ),
                        "name": tool_call_data["name"],
                    },
                    "type": "function",
                    "index": idx,
                }
                for idx, (_, tool_call_data) in enumerate(need_llm_tools)
            ]
            self.dialogue.put(Message(role="assistant", tool_calls=all_tool_calls))

            for result, tool_call_data in need_llm_tools:
                text = result.result
                if text is not None and len(text) > 0:
                    self.dialogue.put(
                        Message(
                            role="tool",
                            tool_call_id=(
                                str(uuid.uuid4())
                                if tool_call_data["id"] is None
                                else tool_call_data["id"]
                            ),
                            content=text,
                        )
                    )

            # Detect duplicate tool calls: if same tool+args was called before, stop recursing
            if not hasattr(self, "_recent_tool_calls"):
                self._recent_tool_calls = set()
            current_calls = frozenset(
                (tc["function"]["name"], tc["function"]["arguments"])
                for tc in all_tool_calls
            )
            if current_calls & self._recent_tool_calls:
                self.logger.bind(tag=TAG).warning(
                    f"Duplicate tool call detected at depth={depth}, forcing final answer"
                )
                self._recent_tool_calls.clear()
                self.dialogue.put(
                    Message(
                        role="system",
                        content="Tool đã gọi trùng lặp và trả kết quả giống nhau. "
                                "KHÔNG gọi lại. Trả lời bé dựa trên kết quả đã có.",
                    )
                )
                self._chat_inner(None, depth=max(depth + 1, 2))
                return
            self._recent_tool_calls.update(current_calls)

            self._chat_inner(None, depth=depth + 1)

    def _report_worker(self):
        """聊天记录上报工作线程"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便定期检查停止事件
                item = self.report_queue.get(timeout=1)
                if item is None:  # 检测毒丸对象
                    break
                try:
                    # 检查线程池状态
                    if self.executor is None:
                        continue
                    # 提交任务到线程池
                    self.executor.submit(self._process_report, *item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Chat history report thread error: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Chat history report worker error: {e}")

        self.logger.bind(tag=TAG).info("Chat history report thread exited")

    def _process_report(self, type, text, audio_data, report_time):
        """处理上报任务"""
        try:
            # 执行异步上报（在事件循环中运行）
            asyncio.run(report(self, type, text, audio_data, report_time))
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Report handling error: {e}")
        finally:
            # 标记任务完成
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.tts_last_stop_time = time.monotonic()
        self._tts_texts_stale = True
        # TTS finished normally → clear story backup (no rollback needed)
        self._rag_story_state_backup = None
        self.logger.bind(tag=TAG).debug("Cleared server speaking state")

    def track_tts_text(self, text: str):
        """Record a TTS segment so ASR can detect echo transcriptions."""
        if text:
            if self._tts_texts_stale:
                self.recent_tts_texts.clear()
                self._tts_texts_stale = False
            self.recent_tts_texts.append(text.lower().strip())
            if len(self.recent_tts_texts) > 10:
                self.recent_tts_texts = self.recent_tts_texts[-10:]

    async def close(self, ws=None):
        """资源清理方法"""
        try:
            # 清理 VAD 连接资源
            if (
                    hasattr(self, "vad")
                    and self.vad
                    and hasattr(self.vad, "release_conn_resources")
            ):
                self.vad.release_conn_resources(self)

            # 清理音频缓冲区
            if hasattr(self, "audio_buffer"):
                self.audio_buffer.clear()

            # 取消超时任务
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None

            # 清理工具处理器资源
            if hasattr(self, "func_handler") and self.func_handler:
                try:
                    await self.func_handler.cleanup()
                except Exception as cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error cleaning up tool handler: {cleanup_error}"
                    )

            # 触发停止事件
            if self.stop_event:
                self.stop_event.set()

            # 清空任务队列
            self.clear_queues()

            # 关闭WebSocket连接
            try:
                if ws:
                    # 安全地检查WebSocket状态并关闭
                    try:
                        if hasattr(ws, "closed") and not ws.closed:
                            await ws.close()
                        elif hasattr(ws, "state") and ws.state.name != "CLOSED":
                            await ws.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await ws.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
                elif self.websocket:
                    try:
                        if (
                                hasattr(self.websocket, "closed")
                                and not self.websocket.closed
                        ):
                            await self.websocket.close()
                        elif (
                                hasattr(self.websocket, "state")
                                and self.websocket.state.name != "CLOSED"
                        ):
                            await self.websocket.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await self.websocket.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
            except Exception as ws_error:
                self.logger.bind(tag=TAG).error(f"Error closing WebSocket: {ws_error}")

            if self.tts:
                await self.tts.close()
            if self.asr:
                await self.asr.close()

            # 最后关闭线程池（避免阻塞）
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception as executor_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error shutting down thread pool: {executor_error}"
                    )
                self.executor = None
            self.logger.bind(tag=TAG).info("Connection resources released")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error closing connection: {e}")
        finally:
            # 确保停止事件被设置
            if self.stop_event:
                self.stop_event.set()

    def clear_queues(self):
        """清空所有任务队列"""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"Queue cleanup start: TTS text={self.tts.tts_text_queue.qsize()}, audio={self.tts.tts_audio_queue.qsize()}"
            )

            # 使用非阻塞方式清空队列
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
                self.report_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            # 重置音频流控器（取消后台任务并清空队列）
            if hasattr(self, "audio_rate_controller") and self.audio_rate_controller:
                self.audio_rate_controller.reset()
                self.logger.bind(tag=TAG).debug("Audio stream controller reset")

            self.logger.bind(tag=TAG).debug(
                f"Queue cleanup done: TTS text={self.tts.tts_text_queue.qsize()}, audio={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_audio_states(self):
        """
        重置所有音频相关状态(VAD + ASR)
        """
        # Reset VAD states
        self.client_audio_buffer.clear()
        self.client_have_voice = False
        self.client_voice_stop = False
        self.client_voice_window.clear()
        self.last_is_voice = False

        # Clear ASR buffers
        self.asr_audio.clear()

        self.logger.bind(tag=TAG).debug("All audio states reset.")

    def chat_and_close(self, text):
        """Chat with the user and then close the connection"""
        try:
            # Use the existing chat method
            self.chat(text)

            # After chat is complete, close the connection
            self.close_after_chat = True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Chat and close error: {str(e)}")

    async def _check_timeout(self):
        """检查连接超时"""
        try:
            while not self.stop_event.is_set():
                last_activity_time = self.last_activity_time
                if self.need_bind:
                    last_activity_time = self.first_activity_time

                # 检查是否超时（只有在时间戳已初始化的情况下）
                if last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    if current_time - last_activity_time > self.timeout_seconds * 1000:
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info("Connection timed out, closing")
                            # 设置停止事件，防止重复处理
                            self.stop_event.set()
                            # 使用 try-except 包装关闭操作，确保不会因为异常而阻塞
                            try:
                                await self.close(self.websocket)
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).error(
                                    f"Error closing connection on timeout: {close_error}"
                                )
                        break
                # 每10秒检查一次，避免过于频繁
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Timeout check task error: {e}")
        finally:
            self.logger.bind(tag=TAG).info("Timeout check task exited")

    @staticmethod
    def _number_sentences(text: str):
        """Number sentences for anchor point tracking.

        Returns (numbered_text, sentence_offsets) where sentence_offsets[i]
        is the character offset of sentence i in the original text.
        """
        import re
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        if len(sentences) <= 1:
            return text, []
        offsets = []
        numbered_parts = []
        pos = 0
        for i, sent in enumerate(sentences, 1):
            offsets.append(pos)
            numbered_parts.append(f"[{i}] {sent}")
            pos += len(sent) + 1
        return "\n".join(numbered_parts), offsets

    def _build_guard_no_story(self, query_name: str = "") -> str:
        """Guard message when no active story exists and query is not story-related."""
        from core.utils.story_registry import story_registry
        all_names = story_registry.get_all_story_names()
        if all_names:
            story_list = ", ".join(all_names)
        else:
            story_list = "(chưa có truyện trong kho)"

        reject_line = ""
        if query_name:
            reject_line = f'Cô chưa biết kể truyện "{query_name}". '
        self.dialogue.put(
            Message(
                role="system",
                content=(
                    f"{reject_line}"
                    "Truyện bé yêu cầu không có trong kho của cô.\n"
                    "Hãy nói với bé rằng cô chưa biết kể truyện đó, "
                    "rồi gợi ý bé chọn từ danh sách truyện cô biết kể.\n"
                    f"DANH SÁCH TRUYỆN CÔ BIẾT KỂ: {story_list}\n"
                    "KHÔNG được tự bịa hay kể truyện từ trí nhớ."
                ),
                is_temporary=True,
            )
        )
        return (
            f"\n\n{reject_line}"
            "Truyện này không có trong kho.\n"
            f"[DANH SÁCH TRUYỆN CÔ BIẾT KỂ]: {story_list}\n"
            "Hãy gợi ý bé chọn truyện từ danh sách trên."
        )

    def _build_random_story_suggestion(self) -> str:
        """Suggest available stories, personalized using memory when available."""
        state = getattr(self, "_rag_story_state", None) or {}
        if not state.get("doc_id"):
            self._rag_story_state = {
                "story_id": None, "doc_id": None,
                "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
            }
        from core.utils.story_registry import story_registry
        all_names = story_registry.get_all_story_names()

        # Parse memory for personalized suggestions
        personalized_hint = ""
        matched_names = []
        try:
            mem = getattr(self, "memory", None)
            if mem and hasattr(mem, "short_memory") and mem.short_memory:
                import json
                mem_data = json.loads(mem.short_memory) if isinstance(mem.short_memory, str) else mem.short_memory
                ho_so = mem_data.get("ho_so_be", {})
                truyen = mem_data.get("truyen", {})
                so_thich = ho_so.get("so_thich", [])
                so_hai = ho_so.get("so_hai", [])
                da_nghe = truyen.get("da_nghe_xong", [])

                if so_thich:
                    include_tags = so_thich if isinstance(so_thich, list) else [so_thich]
                    exclude_tags = so_hai if isinstance(so_hai, list) else ([so_hai] if so_hai else [])
                    matched = story_registry.get_stories_by_tags(include_tags, exclude_tags)
                    matched_names = [c for c, _sid, _t in matched if c not in (da_nghe or [])]
                    if matched_names:
                        personalized_hint = (
                            f"GỢI Ý ƯU TIÊN (phù hợp sở thích bé): {', '.join(matched_names[:3])}\n"
                        )
        except Exception:
            pass

        # Long-term memory: query past preferences for richer personalization
        if getattr(self, "memory_long", None) is not None:
            try:
                import asyncio
                future_lt = asyncio.run_coroutine_threadsafe(
                    self.memory_long.query_memory("bé thích truyện gì, sở thích"),
                    self.loop,
                )
                lt_result = future_lt.result(timeout=3)
                if lt_result:
                    personalized_hint += f"KÝ ỨC CŨ: {lt_result[:200]}\n"
            except Exception:
                pass

        if all_names:
            suggestion = ", ".join(all_names)
        else:
            suggestion = "(chưa có truyện trong kho)"

        # Track suggestions for vague-confirmation resolution
        if matched_names:
            self._last_suggested_stories = matched_names[:3]
        else:
            self._last_suggested_stories = all_names[:4]
        if self._last_suggested_stories:
            self._push_mentioned_story(self._last_suggested_stories[0])

        self.dialogue.put(
            Message(
                role="system",
                content=(
                    "Bé muốn nghe truyện nhưng chưa chọn tên cụ thể.\n"
                    f"{personalized_hint}"
                    "Hãy đọc TÊN các truyện có sẵn bên dưới cho bé nghe, "
                    "rồi hỏi bé muốn nghe truyện nào.\n"
                    f"DANH SÁCH TRUYỆN CÔ BIẾT KỂ: {suggestion}\n"
                    "KHÔNG được kể nội dung truyện. Chỉ liệt kê tên và hỏi bé chọn."
                ),
                is_temporary=True,
            )
        )
        return (
            f"\n\n{personalized_hint}"
            f"[DANH SÁCH TRUYỆN CÔ BIẾT KỂ]: {suggestion}\n"
            "Bé chưa chọn truyện cụ thể. "
            "Hãy đọc tên các truyện trên cho bé nghe và hỏi bé muốn nghe truyện nào."
        )


    def _push_mentioned_story(self, story_name: str):
        pass

    def _scan_response_for_stories(self, text: str):
        pass

    def _pick_random_story(self, exclude: list = None) -> str:
        return ""

    def _resolve_anaphoric_reference(self, query: str) -> str:
        """Resolve anaphoric references like 'con đó', 'truyện đó' using state stack.

        Returns resolved story name, or original query if no anaphoric reference found.
        """
        import re
        q = query.lower().strip()
        _anaphoric_top = [
            r"\bcon đó\b", r"\bcái đó\b", r"\btruyện đó\b", r"\bchuyện đó\b",
            r"\bcâu đó\b", r"\bcái này\b", r"\btruyện này\b",
        ]
        _anaphoric_second = [
            r"\btruyện kia\b", r"\bcái kia\b", r"\bcon kia\b", r"\bchuyện kia\b",
        ]

        for pat in _anaphoric_top:
            if re.search(pat, q):
                if self._last_mentioned_stories:
                    return self._last_mentioned_stories[0]
                return query

        for pat in _anaphoric_second:
            if re.search(pat, q):
                if len(self._last_mentioned_stories) >= 2:
                    return self._last_mentioned_stories[1]
                elif self._last_mentioned_stories:
                    return self._last_mentioned_stories[0]
                return query

        return query

    @staticmethod
    def _extract_story_name(query: str) -> str:
        """Extract story name from ASR query by stripping request prefixes/suffixes.

        ASR transcription often produces severely garbled output like:
        "kẻ cơ y chiến vủa sự thích chầu câu" (user meant "sự tích trầu cau")
        "<unk>được rồi kẻ tôi câu chuyện về cái thiết dụ" (user meant "cây huyết dụ")

        Strategy:
        1. Try exact prefix match first (handles clean ASR).
        2. If that fails, look for story-name anchor words ("sự tích", "về", "truyện")
           and extract everything after them.
        3. Fall back to stripping only known junk from start/end.
        """
        import re

        def strip_suffixes(text: str) -> str:
            _suffixes = [
                "được không", "đi nha", "đi nhé", "nha", "nhé", "đi",
                "cho bé", "cho tôi", "giúp cô",
            ]
            for s in _suffixes:
                if text.endswith(s):
                    text = text[:-len(s)].strip()
                    break
            return text
        q = query.lower().strip()

        # Remove <unk> tokens from ASR
        q = re.sub(r"<unk>", "", q).strip()
        # Remove stray single characters at word boundaries (common ASR artifacts)
        q = re.sub(r"\b[a-zàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]\b", "", q)
        q = re.sub(r"\s+", " ", q).strip()

        # ── Strategy 1: Exact prefix match (clean or semi-clean ASR) ──
        _prefixes = [
            "được rồi kể tôi câu chuyện về",
            "được rồi kẻ tôi câu chuyện về",
            "rồi kể tôi câu chuyện về",
            "rồi kẻ tôi câu chuyện về",
            "kể tôi câu chuyện về",
            "kẻ tôi câu chuyện về",
            "cho tôi câu chuyện về",
            "kể cho tôi câu chuyện về",
            "kể cho bé câu chuyện về",
            "kể câu chuyện về",
            "kẻ câu chuyện về",
            "xin chào kể câu chuyện về",
            "xin chào kẻ câu chuyện về",
            "xin chào hãy kể câu chuyện về",
            "cho tôi truyện về",
            "cho tôi nghe truyện về",
            "kể chuyện về",
            "kẻ chuyện về",
            "chuyển qua",
            "đổi truyện sang",
            "đổi sang",
            "nghe truyện về",
            "nghe chuyện về",
            "câu chuyện về",
            "chuyện về",
            "truyện về",
            "kể truyện",
            "kể chuyện",
            "kẻ chuyện",
            "kẻ truyện",
            "nghe truyện",
            "nghe chuyện",
            "cho tôi câu chuyện",
            "cho tôi truyện",
            "kể cho tôi",
            "kể tôi",
            "kẻ tôi",
        ]

        for prefix in _prefixes:
            if q.startswith(prefix):
                extracted = q[len(prefix):].strip()
                if len(extracted) >= 2:
                    return strip_suffixes(extracted)
                break

        # ── Strategy 2: Anchor-based extraction ──
        # Look for "sự tích/sự thích/sở thích" + everything after
        anchor_match = re.search(
            r"(sự tích|sự thích|sở thích|sử thích|sư tích|sứ tích|su tich"
            r"|cổ tích|co tich|cỗ tích)",
            q
        )
        if anchor_match:
            extracted = q[anchor_match.start():].strip()
            from core.utils.story_registry import _SU_TICH_PREFIXES
            core_after_prefix = _SU_TICH_PREFIXES.sub("", extracted).strip()
            if len(core_after_prefix) < 3:
                return strip_suffixes(q)
            return strip_suffixes(extracted)

        # Look for "về" + everything after (e.g., "câu chuyện về trái sầu riêng")
        ve_match = re.search(r"\bvề\s+(.+)", q)
        if ve_match:
            extracted = ve_match.group(1).strip()
            if len(extracted) >= 2:
                return strip_suffixes(extracted)

        # Look for "chuyện/truyện" + everything after
        story_word_match = re.search(r"(?:câu chuyện|chuyện|truyện)\s+(.+)", q)
        if story_word_match:
            extracted = story_word_match.group(1).strip()
            # Remove "về" if it starts the extracted portion
            if extracted.startswith("về "):
                extracted = extracted[3:].strip()
            if len(extracted) >= 2:
                return strip_suffixes(extracted)

        # ── Strategy 3: Strip leading/trailing junk, return remainder ──
        _leading_junk = [
            "được rồi", "rồi", "ừ", "ờ", "à", "ừm", "tô",
            "xin chào", "chào", "bạn ơi", "cô ơi",
            "tôi muốn nghe", "tôi muốn", "muốn", "hãy",
        ]
        result = q
        for junk in _leading_junk:
            if result.startswith(junk):
                result = result[len(junk):].strip()
                break

        if len(result) < 2:
            return query.strip()

        return strip_suffixes(result)

    _VI_CLASSIFIERS = frozenset({
        "con", "cay", "cai", "nguoi", "anh", "chi", "em",
        "ong", "ba", "chim", "cua", "nha",
    })

    _GENERIC_STOP_WORDS = frozenset({
        "nao", "gi", "hay", "khong", "co", "di", "nha", "nhe",
        "duoc", "roi", "the", "ma", "la", "thi", "cung",
        "truoc", "do", "sau", "nay", "day", "mot", "cai",
        "ve", "cho", "voi", "cua", "nhu", "lam", "qua",
        "hon", "nua", "lai", "len", "ra", "vao",
        "co", "chu", "be", "oi", "a", "u", "o",
    })

    @staticmethod
    def _is_generic_query(search_query: str) -> bool:
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', search_query.lower())
        normalized = ''.join(c for c in nfkd if not unicodedata.combining(c))
        words = set(normalized.split()) - ConnectionHandler._GENERIC_STOP_WORDS
        return len(words) == 0

    @staticmethod
    def _keyword_validates_story(search_query: str, story_id: str, story_name: str) -> bool:
        """Check >= 1 meaningful word overlap between query and story metadata.

        Normalize both sides to unaccented lowercase, strip "su tich" prefix,
        remove Vietnamese classifiers, then check for any remaining overlap.
        """
        from core.utils.story_registry import _SU_TICH_PREFIXES
        import unicodedata, re

        def remove_diacritics(text: str) -> str:
            nfkd = unicodedata.normalize('NFKD', text.lower())
            return ''.join(c for c in nfkd if not unicodedata.combining(c))

        def to_word_set(text: str) -> set:
            normalized = remove_diacritics(text)
            return {w for w in normalized.split() if len(w) >= 2}

        q = search_query.lower().strip()
        q_core = _SU_TICH_PREFIXES.sub("", q).strip()
        q_words = to_word_set(q_core)
        if not q_words:
            return False

        name_spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', story_name)
        name_spaced = re.sub(r'[_\-]', ' ', name_spaced).lower()
        name_core = _SU_TICH_PREFIXES.sub("", name_spaced).strip()

        id_spaced = story_id.replace('-', ' ').lower()
        id_core = _SU_TICH_PREFIXES.sub("", id_spaced).strip()

        story_words = to_word_set(name_core) | to_word_set(id_core)
        if not story_words:
            return False

        meaningful_match = (q_words & story_words) - ConnectionHandler._VI_CLASSIFIERS
        return len(meaningful_match) >= 1

    @classmethod
    def _fuzzy_match_story(cls, extracted_query: str) -> tuple:
        """Try to match extracted query against known story names using character overlap.

        Delegates to the global StoryRegistry (auto-populated from Qdrant).
        Returns (canonical_search_term, story_id) if confident match found,
        otherwise (None, None).
        """
        from core.utils.story_registry import story_registry
        return story_registry.fuzzy_match(extracted_query)

    @staticmethod
    def _find_split_point(text: str, target: int) -> int:
        """Find the best paragraph or sentence boundary near *target* char index."""
        for sep in ["\n\n", "\n", ". ", "? ", "! "]:
            pos = text.rfind(sep, 0, target + 50)
            if pos > target * 0.4:
                return pos + len(sep)
        return target

    def _classify_intent(self, query: str) -> str:
        """Semantic intent classification for storyteller bot.

        Returns one of:
            "tool"        - Weather/time/music requests (bypass RAG entirely)
            "stop"        - User wants to stop the current story
            "greeting"    - Pure greeting with no active story (ask child to pick)
            "random_story" - User wants a different story but no specific name
            "new_story"   - User requests a new/different story
            "story_question" - Question about the CURRENT story context
            "continue"    - User wants the story to continue
            "out_of_scope" - Everything else (redirect to story)
        """
        q = query.lower().strip()
        q_padded = f" {q} "

        # ── Tool Detection (weather, time, music) ──
        _tool_patterns = [
            "mấy giờ", "ngày mấy", "hôm nay", "thứ mấy",
            "ngày bao nhiêu", "ngày mai", "hôm qua", "bây giờ",
            "thời tiết", "trời mưa", "nắng không", "lạnh không",
            "nóng không", "trời nắng", "trời lạnh", "thoi tiet",
            "mở nhạc", "phát nhạc", "nghe nhạc", "bài hát",
            "bật nhạc", "hát đi", "nghe bài",
        ]
        if any(p in q for p in _tool_patterns):
            return "tool"

        # ── Stop Detection ──
        _stop_patterns = [
            "dừng lại", "dung lai", "thôi", "nghe đủ rồi",
            "không kể nữa", "không nghe nữa", "dừng", "ngừng",
            "stop", "đủ rồi", "thôi đi", "cô dừng", "dừng kể",
        ]
        if any(p in q for p in _stop_patterns):
            # If the query ALSO contains a new-story request, the user wants
            # to switch stories, not just stop.  E.g. "dừng lại kể truyện tấm cám"
            _has_story_word = any(p in q for p in [
                "kể", "kẻ", "chuyện", "truyện",
                "sự tích", "sự thích", "sở thích", "sử thích",
                "cổ tích", "nghe truyện", "nghe chuyện",
            ])
            if not _has_story_word:
                return "stop"

        # ── Greeting Detection (no active story → ask child what story) ──
        _greeting_patterns = [
            "xin chào", "chào cô", "chào bé", "hello", "hi ",
            "chào buổi", "chào ngày",
        ]
        state = getattr(self, "_rag_story_state", None)
        has_active_story = state and state.get("doc_id")
        is_greeting = any(p in q for p in _greeting_patterns)

        # Pure greeting (no story-related words mixed in)
        _has_story_word = any(p in q for p in [
            "kể", "kẻ", "chuyện", "truyện",
            "sự tích", "sự thích", "sở thích", "sử thích",
            "tựu thích", "xựu thích",
            "cổ tích", "nghe truyện", "nghe chuyện",
        ])
        if is_greeting and not _has_story_word and not has_active_story:
            return "greeting"

        # ── Random Story Intent (no specific name) ──
        _random_story_patterns = [
            "chuyện khác", "truyện khác", "kể cái khác",
            "kể chuyện khác", "nghe cái khác", "chán rồi",
            "không muốn nghe", "không thích truyện",
            "đổi truyện", "chuyển qua",
            "có truyện gì", "có chuyện gì", "có truyện nào",
            "có chuyện nào", "truyện gì", "chuyện gì",
            "kể gì được", "biết kể gì", "có gì kể",
            "có câu chuyện nào", "có câu truyện nào",
        ]
        if any(p in q for p in _random_story_patterns):
            return "random_story"

        # ── Continue Intent (MUST be before new_story) ──
        _continue_patterns = [
            "kể tiếp", "ke tiep", "tiếp đi", "tiep di",
            "rồi sao", "tiếp tục", "kể nữa", "tiếp theo",
            "tiep theo", "còn gì nữa", "kể đi", "sau đó",
            "xong rồi sao", "hết chưa", "kế tiếp", "kể tiết",
            "kế tiệp", "kễ tiếp", "kê tiếp", "kể tiệp",
            "tiếp tiếp",
        ]
        if any(p in q for p in _continue_patterns):
            return "continue"

        # ── Confirm Suggested Story (acts as continue with last suggested) ──
        _confirm_patterns = [
            "chuyện đó", "truyện đó", "cái đó",
            "được đó", "ừ đi", "ừ kể",
        ]
        if self._last_suggested_stories and any(p in q for p in _confirm_patterns):
            return "continue"
        _new_story_patterns = [
            "kể chuyện", "kể truyện", "kể câu chuyện", "kể câu truyện",
            "kẻ chuyện", "kẻ câu chuyện", "kễ chuyện", "kê chuyện",
            "câu chuyện về", "chuyện về", "câu chuyện",
            "sự tích", "su tich", "sự thích", "sư tích", "sứ tích",
            "sở thích", "sử thích", "tựu thích", "xựu thích",
            "cổ tích", "co tich", "cỗ tích",
            "tìm truyện",
            "nghe truyện", "nghe chuyện",
            "cho tôi câu chuyện", "cho tôi truyện",
            "cho câu chuyện", "cho truyện",
        ]
        if any(p in q for p in _new_story_patterns):
            return "new_story"

        # Fallback: detect scattered story-request words from garbled ASR
        # e.g. "kể kho chuyện ...", "à cho câu chuyện ..."
        _has_request_verb = any(w in q_padded for w in (
            " kể ", " kẻ ", " cho ", " nghe ",
        ))
        _has_story_noun = any(w in q for w in (
            "chuyện", "truyện",
        ))
        if _has_request_verb and _has_story_noun:
            return "new_story"

        # ── Story Question Intent (only valid if active story) ──
        if has_active_story:
            _personal_patterns = [
                "con là ai", "con la ai", "bé là ai", "be la ai",
                "tên con là", "ten con la", "tên bé là", "ten be la",
                "biết con là", "biet con la", "biết bé là", "biet be la",
                "nhớ con không", "nho con khong", "nhớ bé không", "nho be khong",
                "biết con không", "biet con khong",
                "con tên gì", "con ten gi", "bé tên gì", "be ten gi",
            ]
            if any(p in q for p in _personal_patterns):
                return "out_of_scope"

            q_stripped = q.rstrip("?!. ")
            _is_question_ending = (
                len(q) > 5
                and q_stripped.endswith((
                    " gì", " không", " hả", " hử", " chưa",
                    " sao", " đâu", " nào", " ai",
                ))
            )
            _has_mid_question_word = (
                len(q) > 12
                and any(
                    w in q_padded
                    for w in (
                        " gì ", " nào ", " sao ", " đâu ",
                        " ai ", " mấy ", " bao nhiêu ",
                        " tại sao ", " vì sao ", " như thế nào ",
                    )
                )
            )
            _question_starters = [
                "tại sao", "vì sao", "ai là", "là cái gì",
                "là gì", "là sao", "là ai", "nghĩa là",
                "có nghĩa", "giải thích", "ở đâu", "bao giờ",
                "có phải", "phải không", "có thật", "thật không",
            ]
            _has_question_starter = any(p in q for p in _question_starters)

            if _is_question_ending or _has_mid_question_word or _has_question_starter:
                return "story_question"

            # Short utterances (acknowledgments) during active story → continue
            if len(q) <= 8:
                return "continue"

        # ── Out-of-Scope: anything not matching above ──
        return "out_of_scope"

    def _llm_reclassify_intent(self, query: str) -> str:
        """Fallback: dung LLM chinh de phan loai lai khi pattern matcher tra ve out_of_scope."""
        if not self.llm:
            return "out_of_scope"
        system_prompt = (
            "Phân loại ý định của bé (trẻ em 5-10 tuổi nói chuyện với cô giáo kể chuyện).\n"
            "Trả lời ĐÚNG 1 từ: random_story / new_story / greeting / out_of_scope\n"
            "- random_story: bé muốn nghe truyện gì đó (không chỉ định tên cụ thể)\n"
            "- new_story: bé yêu cầu một truyện cụ thể (có tên/mô tả rõ)\n"
            "- greeting: chào hỏi\n"
            "- out_of_scope: không liên quan đến truyện\n"
            "Chỉ trả lời 1 từ."
        )
        user_prompt = query.strip()
        try:
            result = self.llm.response_no_stream(system_prompt, user_prompt)
            result = result.strip().lower().split()[0] if result else ""
            if result in ("random_story", "new_story", "greeting"):
                return result
        except Exception:
            pass
        return "out_of_scope"

    def _get_inline_rag_context(self, query: str) -> str:
        """RAG Inline: Semantic Intent Router + Doc-Expand + Sliding Window.

        Layers:
        1. Intent Classification (semantic, no keyword maps)
        2. Filtered Search: Qdrant search with optional story_id filter
        3. Doc-Expand: get all parts of matched story via doc_id
        4. Sliding Window: resume from last_part_index
        5. Budget: truncate to max_context_chars

        Stores result in self._current_rag_context (NOT in query).
        """
        rag_section = self.config.get("RAG", {})
        rag_inline_config = rag_section.get("inline", {})

        if not rag_inline_config.get("enabled", False):
            self.logger.bind(tag=TAG).debug("RAG Inline: disabled")
            return ""

        # ── Acquire provider + lazy-build story registry BEFORE intent routing ──
        plugin_name = rag_inline_config.get("qdrant_plugin", "search_from_qdrant")
        rag_config = self.config.get("plugins", {}).get(plugin_name, {})
        if isinstance(rag_config, str):
            try:
                rag_config = json.loads(rag_config)
            except Exception:
                rag_config = {}

        if not rag_config:
            self.logger.bind(tag=TAG).warning(
                f"RAG Inline: plugin config '{plugin_name}' not found"
            )
            return ""

        from core.utils.rag_plugin_config import merge_llm_keys_into_rag_config
        rag_config = merge_llm_keys_into_rag_config(rag_config, self.config)
        rag_config = dict(rag_config)
        rag_config["rag_provider"] = "qdrant"

        if self.loop is None or not self.loop.is_running():
            self.logger.bind(tag=TAG).warning("RAG Inline: no running event loop")
            return ""

        from core.utils.rag_manager import inline_rag_manager
        from core.utils.story_registry import story_registry
        provider = inline_rag_manager.get_provider(rag_config)

        # Lazy-build story registry if not yet populated
        if not story_registry.is_built and hasattr(provider, "list_unique_stories"):
            try:
                future_build = asyncio.run_coroutine_threadsafe(
                    story_registry.build(provider), self.loop,
                )
                future_build.result(timeout=5)
            except Exception as e:
                self.logger.bind(tag=TAG).warning(
                    f"StoryRegistry lazy build failed: {e}"
                )

        base_threshold = float(rag_inline_config.get(
            "score_threshold", rag_config.get("score_threshold", 0.30)
        ))
        max_context_chars = int(rag_inline_config.get("max_context_chars", 12000))

        # ── Layer 0: Inject available story list into system prompt (once) ──
        if not getattr(self, "_story_list_injected", False):
            try:
                from core.utils.story_registry import story_registry
                all_names = story_registry.get_all_story_names()
                if all_names:
                    story_list = ", ".join(all_names)
                    current_prompt = self.prompt or ""
                    if "<available_stories>" not in current_prompt:
                        updated = (
                            current_prompt +
                            f"\n\n<available_stories>\n"
                            f"Danh sách truyện cô biết kể: {story_list}\n"
                            f"</available_stories>"
                        )
                        self.change_system_prompt(updated)
                        self.logger.bind(tag=TAG).info(
                            f"Injected {len(all_names)} stories into system prompt"
                        )
                    self._story_list_injected = True
            except Exception as e:
                self.logger.bind(tag=TAG).warning(f"Story list injection failed: {e}")

        # ── Layer 1: Semantic Intent Classification ──
        intent = self._classify_intent(query)
        state = getattr(self, "_rag_story_state", None) or {}
        matched_story_id = None
        is_continue = False
        search_query = query  # default; overridden for new_story intent

        # ── Layer 1b: LLM fallback khi pattern matcher tra ve out_of_scope ──
        if intent == "out_of_scope" and not state.get("story_id"):
            intent = self._llm_reclassify_intent(query)
            if intent != "out_of_scope":
                self.logger.bind(tag=TAG).info(
                    f"RAG Intent: LLM reclassified to '{intent}'"
                )

        self.logger.bind(tag=TAG).info(
            f"RAG Intent: '{intent}' for query: {query[:50]}"
        )

        if intent == "tool":
            # Tools (weather/time/music) bypass RAG entirely
            return ""

        elif intent == "stop":
            self.logger.bind(tag=TAG).info("RAG Intent: stop → clearing story state")
            self._rag_story_state = {
                "story_id": None, "doc_id": None,
                "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
            }
            return ""

        elif intent == "greeting":
            self.logger.bind(tag=TAG).info("RAG Intent: greeting → ask child to pick story")
            # Dynamically list story names from registry
            from core.utils.story_registry import story_registry
            all_names = story_registry.get_all_story_names()
            if all_names:
                import random
                samples = random.sample(all_names, min(4, len(all_names)))
                suggestion = ", ".join(samples)
            else:
                suggestion = "(chưa có truyện trong kho)"
            self.dialogue.put(
                Message(
                    role="system",
                    content=(
                        "[BẮT BUỘC] Bé chào hỏi. KHÔNG được tự kể bất kỳ câu chuyện nào.\n"
                        "Chào bé lại thân thiện, rồi HỎI bé muốn nghe truyện gì.\n"
                        f"Gợi ý tên truyện từ kho: {suggestion}...\n"
                        "KHÔNG ĐƯỢC kể truyện, KHÔNG ĐƯỢC bịa nhân vật."
                    ),
                )
            )
            return (
                "\n\n[TRUYỆN TỪ KHO]: CHƯA CHỌN. "
                "Bé chưa chọn truyện. Chào bé rồi hỏi bé muốn nghe truyện gì."
            )

        elif intent == "random_story":
            return self._build_random_story_suggestion()

        elif intent == "new_story":
            # Clear old state, perform fresh RAG search
            self._rag_story_state = {
                "story_id": None, "doc_id": None,
                "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
            }
            matched_story_id = None
            is_continue = False
            # Resolve anaphoric references ("con đó", "truyện kia") via state stack
            resolved = self._resolve_anaphoric_reference(query)
            if resolved != query:
                self.logger.bind(tag=TAG).info(
                    f"RAG Intent: anaphoric resolved '{query[:30]}' → '{resolved}'"
                )
                search_query = resolved
            else:
                search_query = self._extract_story_name(query)
            self.logger.bind(tag=TAG).info(
                f"RAG Intent: new_story | raw='{query[:50]}' "
                f"→ search='{search_query[:50]}'"
            )
            if len(search_query.strip()) <= 2 or self._is_generic_query(search_query):
                if self._last_suggested_stories:
                    target = self._last_suggested_stories[0]
                    self.logger.bind(tag=TAG).info(
                        f"RAG Intent: new_story generic (already suggested) → "
                        f"auto-selecting: '{target}'"
                    )
                    search_query = target
                else:
                    target = self._pick_random_story()
                    if target:
                        self.logger.bind(tag=TAG).info(
                            f"RAG Intent: new_story generic → random pick: '{target}'"
                        )
                        search_query = target
                        self._last_suggested_stories = [target]
                        self._push_mentioned_story(target)
                    else:
                        return self._build_random_story_suggestion()

            # Try fuzzy alias match from StoryRegistry BEFORE Qdrant search.
            # Handles ASR garble like "tô hú" → "tu hú", "chim đa đa" → registry hit.
            fuzzy_canonical, fuzzy_sid = self._fuzzy_match_story(search_query)
            if fuzzy_sid:
                matched_story_id = fuzzy_sid
                search_query = fuzzy_canonical or search_query
                self.logger.bind(tag=TAG).info(
                    f"RAG Intent: new_story → fuzzy alias match: "
                    f"story_id='{fuzzy_sid}', canonical='{fuzzy_canonical}'"
                )

        elif intent == "continue":
            if state.get("story_id") and state.get("doc_id"):
                matched_story_id = state["story_id"]
                is_continue = True
                _tail = state.get("last_narrated_tail", "")
                if _tail:
                    self.dialogue.put(
                        Message(
                            role="system",
                            content=(
                                f"[VỊ TRÍ HIỆN TẠI] Đoạn cuối cùng cô vừa kể: "
                                f"'...{_tail}'. "
                                "Tiếp tục từ ĐÂY, KHÔNG lặp lại, KHÔNG nhảy."
                            ),
                            is_temporary=True,
                        )
                    )
                self.logger.bind(tag=TAG).info(
                    f"RAG Intent: continue → resuming story_id={matched_story_id}"
                )
            else:
                if self._last_suggested_stories:
                    target = self._last_suggested_stories[0]
                    self.logger.bind(tag=TAG).info(
                        f"RAG Intent: continue (no active story) → "
                        f"auto-selecting last suggested: '{target}'"
                    )
                    self._rag_story_state = {
                        "story_id": None, "doc_id": None,
                        "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
                    }
                    search_query = target
                    matched_story_id = None
                    is_continue = False
                else:
                    target = self._pick_random_story()
                    if target:
                        self.logger.bind(tag=TAG).info(
                            f"RAG Intent: continue (no active story, no suggestions) → "
                            f"random pick: '{target}'"
                        )
                        self._rag_story_state = {
                            "story_id": None, "doc_id": None,
                            "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
                        }
                        search_query = target
                        matched_story_id = None
                        is_continue = False
                        self._last_suggested_stories = [target]
                        self._push_mentioned_story(target)
                    else:
                        return self._build_guard_no_story()

        elif intent == "story_question":
            # Provide current story context so LLM can answer, WITHOUT advancing position
            if state.get("doc_id"):
                self.logger.bind(tag=TAG).info(
                    "RAG Intent: story_question → providing context (no position advance)"
                )
                self.dialogue.put(
                    Message(
                        role="system",
                        content=(
                            "[Lưu ý] Bé đang hỏi câu hỏi VỀ TRUYỆN đang kể. "
                            "TRẢ LỜI ngắn gọn dựa trên context truyện được cung cấp. "
                            "KHÔNG bịa thêm thông tin ngoài context. "
                            "Sau khi trả lời, hỏi bé có muốn nghe tiếp không."
                        ),
                        is_temporary=True,
                    )
                )
                try:
                    if not provider:
                        return ""
                    sq_doc_id = state["doc_id"]
                    sq_story_id = state.get("story_id", "")
                    future_sq = asyncio.run_coroutine_threadsafe(
                        provider.get_chunks_by_doc_id(sq_doc_id), self.loop,
                    )
                    sq_parts = future_sq.result(timeout=8)
                    if not sq_parts:
                        return ""

                    sq_last_idx = state.get("last_part_index", 0)
                    sq_sub_off = state.get("sub_offset", 0)

                    sq_text = sq_parts[sq_last_idx].get("content", "") if sq_last_idx < len(sq_parts) else ""
                    if sq_sub_off > 0 and sq_sub_off < len(sq_text):
                        sq_text = sq_text[:sq_sub_off]

                    if not sq_text:
                        sq_text = sq_parts[max(0, sq_last_idx - 1)].get("content", "") if sq_last_idx > 0 else ""

                    sq_text = sq_text[:max_context_chars] if sq_text else ""
                    context = (
                        f"[TRUYỆN ĐANG KỂ – context cho câu hỏi]\n{sq_text}\n[HẾT]\n"
                        "Trả lời dựa trên context trên. KHÔNG bịa thêm."
                    )
                    self.logger.bind(tag=TAG).info(
                        f"RAG Inline: story_question context chars={len(sq_text)} "
                        f"story='{sq_story_id}' part={sq_last_idx} (position unchanged)"
                    )
                    return context
                except Exception as e:
                    self.logger.bind(tag=TAG).warning(f"story_question context error: {e}")
                    return ""
            else:
                return self._build_guard_no_story()

        elif intent == "out_of_scope":
            self.dialogue.put(
                Message(
                    role="system",
                    content=(
                        "Kiểm tra <memory> trước khi trả lời. "
                        "Nếu không có thông tin trong kho truyện hoặc <memory>, "
                        "nói 'Ôi cô chưa biết nè' rồi chuyển hướng về truyện. "
                        "KHÔNG sáng tác hay dùng kiến thức huấn luyện."
                    ),
                    is_temporary=True,
                )
            )
            if state.get("doc_id"):
                self.logger.bind(tag=TAG).info(
                    "RAG Intent: out_of_scope during active story → guardrail + ask to continue"
                )
            else:
                self.logger.bind(tag=TAG).info(
                    "RAG Intent: out_of_scope, no active story → guardrail"
                )
            return ""

        try:
            # ── Layer 2: Filtered Search ──
            if is_continue and matched_story_id:
                # "kể tiếp" — skip search, reuse stored doc_id
                state = self._rag_story_state
                doc_id = state.get("doc_id")
                if not doc_id:
                    self.logger.bind(tag=TAG).info(
                        "RAG Inline: continue but no doc_id in state, falling back to search"
                    )
                    is_continue = False

            if not is_continue:
                future = asyncio.run_coroutine_threadsafe(
                    provider.search(
                        query=search_query,
                        top_k=1,
                        score_threshold=base_threshold,
                        story_id=matched_story_id,
                    ),
                    self.loop,
                )
                results = future.result(timeout=5)

                if not results:
                    self.logger.bind(tag=TAG).info(
                        f"RAG Inline: no results above threshold={base_threshold} "
                        f"for search_query: {search_query[:50]} (story_id={matched_story_id})"
                    )
                    if state.get("doc_id") and intent == "out_of_scope":
                        matched_story_id = state.get("story_id")
                        doc_id = state.get("doc_id")
                        is_continue = True
                    elif state.get("doc_id"):
                        self.dialogue.put(
                            Message(
                                role="system",
                                content=(
                                    "[GUARD] Không tìm thấy câu trả lời trong kho truyện. "
                                    "Từ chối khéo câu hỏi và tiếp tục kể truyện."
                                ),
                                is_temporary=True,
                            )
                        )
                        matched_story_id = state.get("story_id")
                        doc_id = state.get("doc_id")
                        is_continue = True
                    else:
                        self._failed_stories.add(search_query.lower())
                        for _retry_i in range(3):
                            retry_target = self._pick_random_story(
                                exclude=self._last_suggested_stories + [search_query]
                            )
                            if not retry_target or retry_target.lower() == search_query.lower():
                                break
                            self.logger.bind(tag=TAG).info(
                                f"RAG Inline: no content for '{search_query}', "
                                f"retry #{_retry_i+1} with '{retry_target}'"
                            )
                            search_query = retry_target
                            matched_story_id = None
                            self._last_suggested_stories = [retry_target]
                            self._push_mentioned_story(retry_target)
                            fuzzy_canonical, fuzzy_sid = self._fuzzy_match_story(search_query)
                            if fuzzy_sid:
                                matched_story_id = fuzzy_sid
                                search_query = fuzzy_canonical or search_query
                            future = asyncio.run_coroutine_threadsafe(
                                provider.search(
                                    query=search_query,
                                    top_k=1,
                                    score_threshold=base_threshold,
                                    story_id=matched_story_id,
                                ),
                                self.loop,
                            )
                            results = future.result(timeout=5)
                            if results:
                                break
                            self._failed_stories.add(retry_target.lower())
                        if not results:
                            self.dialogue.put(
                                Message(
                                    role="system",
                                    content=(
                                        "[BẮT BUỘC] Kho truyện của cô không tìm thấy nội dung. "
                                        "KHÔNG ĐƯỢC kể hay bịa truyện. Chỉ được nói: "
                                        "'Ôi, cô chưa nhớ truyện đó. Con chọn truyện khác nha!' "
                                        "rồi gợi ý 2-3 tên truyện từ danh sách."
                                    ),
                                    is_temporary=True,
                                )
                            )
                            return ""
                if results:
                    top_result = results[0]
                    doc_id = top_result.metadata.get("doc_id", "")
                    found_story_id = top_result.metadata.get("story_id", matched_story_id or "")
                    found_story_name = top_result.metadata.get("story_name", "")
                    result_score = getattr(top_result, "score", 0.0)

                    self.logger.bind(tag=TAG).info(
                        f"RAG Inline: top result score={result_score:.3f} "
                        f"story_id='{found_story_id}' for search_query='{search_query[:40]}'"
                    )

                    if intent == "new_story":
                        if matched_story_id and found_story_id == matched_story_id:
                            pass
                        elif not self._keyword_validates_story(
                            search_query, found_story_id, found_story_name
                        ):
                            # Last chance: check fuzzy alias match against the found story
                            from core.utils.story_registry import story_registry
                            _, alias_sid = story_registry.fuzzy_match(search_query)
                            if alias_sid and alias_sid == found_story_id:
                                self.logger.bind(tag=TAG).info(
                                    f"RAG Inline: keyword mismatch bypassed via alias match "
                                    f"for story='{found_story_id}'"
                                )
                            elif self._is_generic_query(search_query):
                                return self._build_random_story_suggestion()
                            else:
                                self.logger.bind(tag=TAG).info(
                                    f"RAG Inline: keyword mismatch — query='{search_query[:30]}' "
                                    f"vs story='{found_story_id}' — từ chối kể"
                                )
                                return self._build_guard_no_story(query_name=search_query)

                    if not matched_story_id:
                        matched_story_id = found_story_id

            # ── Layer 3: Doc-Expand ──
            if not doc_id:
                self.logger.bind(tag=TAG).warning("RAG Inline: no doc_id found")
                return ""

            future_chunks = asyncio.run_coroutine_threadsafe(
                provider.get_chunks_by_doc_id(doc_id),
                self.loop,
            )
            all_parts = future_chunks.result(timeout=8)

            if not all_parts:
                self.logger.bind(tag=TAG).info(
                    f"RAG Inline: no parts found for doc_id={doc_id}"
                )
                return ""

            total_parts = len(all_parts)

            # ── Layer 4: Sliding Window ──
            state = getattr(self, "_rag_story_state", {}) or {}
            sub_offset = 0
            if is_continue and state.get("story_id") == matched_story_id:
                sub_offset = state.get("sub_offset", 0)
                if sub_offset > 0:
                    start_index = state.get("last_part_index", 0)
                else:
                    start_index = state.get("last_part_index", -1) + 1
            else:
                start_index = 0

            if start_index >= total_parts:
                if is_continue:
                    self.logger.bind(tag=TAG).info(
                        f"RAG Inline: story '{matched_story_id}' already finished "
                        f"({total_parts} parts). Notifying user."
                    )
                    template = rag_inline_config.get(
                        "story_finished_template",
                        "[THÔNG BÁO] Truyện '{story_id}' đã kể XONG toàn bộ. "
                        "KHÔNG được bịa thêm. Hỏi bé muốn nghe truyện khác không.",
                    )
                    notice = template.format(story_id=matched_story_id)
                    self._rag_story_state = {
                        "story_id": None, "doc_id": None,
                        "last_part_index": -1, "total_parts": 0, "sub_offset": 0,
                    }
                    return notice
                else:
                    start_index = 0

            # ── Layer 4b: Overlap from previous section ──
            overlap_text = ""
            if is_continue and (start_index > 0 or sub_offset > 0):
                if sub_offset > 0:
                    prev_text = all_parts[start_index].get("content", "")[:sub_offset]
                elif start_index > 0:
                    prev_text = all_parts[start_index - 1].get("content", "")
                else:
                    prev_text = ""
                if prev_text:
                    overlap_text = prev_text[-500:]

            # ── Layer 5: Budget + Sub-chunk splitting ──
            text_parts = []
            chars_used = 0
            last_read_index = start_index - 1

            for part in all_parts[start_index:]:
                part_text = part.get("content", "")
                if chars_used + len(part_text) > max_context_chars and text_parts:
                    break
                text_parts.append(part_text)
                chars_used += len(part_text)
                last_read_index = part["part_index"]

            if not text_parts:
                self.logger.bind(tag=TAG).info("RAG Inline: no text within budget")
                return ""

            full_text = "\n\n".join(text_parts)

            # Apply sub_offset if resuming mid-chunk
            if sub_offset > 0 and sub_offset < len(full_text):
                full_text = full_text[sub_offset:]

            # Sub-chunk split: if text is too long for one detailed narration,
            # split at paragraph/sentence boundary and save sub_offset for next turn
            sub_split_threshold = int(max_context_chars * 0.6)
            new_sub_offset = 0
            if len(full_text) > sub_split_threshold:
                cut = self._find_split_point(
                    full_text, sub_split_threshold
                )
                if cut > 0 and cut < len(full_text) - 100:
                    new_sub_offset = (sub_offset + cut) if sub_offset else cut
                    full_text = full_text[:cut]

            if len(full_text) > max_context_chars:
                full_text = full_text[:max_context_chars]

            # Anchor Point Indexing: number sentences for completion tracking
            numbered_text, sentence_offsets = self._number_sentences(full_text)
            if sentence_offsets:
                self._rag_story_state["_sentence_offsets"] = sentence_offsets
                self._rag_story_state["_chunk_raw_text"] = full_text
                full_text = numbered_text

            # Prepend overlap so LLM knows what was already narrated
            if overlap_text:
                full_text = (
                    f"[ĐÃ KỂ TRƯỚC ĐÓ]\n...{overlap_text}\n[HẾT ĐÃ KỂ]\n\n"
                    + full_text
                )

            # End-of-story marker so LLM knows whether to stop or continue
            has_more = (last_read_index < total_parts - 1) or (new_sub_offset > 0)
            if has_more:
                remaining = total_parts - 1 - last_read_index
                full_text += (
                    f"\n\n[CÒN TIẾP — còn {remaining} phần nữa. "
                    "Kể HẾT nội dung ở trên rồi hãy hỏi bé. "
                    "KHÔNG ĐƯỢC tự bịa phần tiếp theo.]"
                )
            else:
                full_text += (
                    "\n\n[HẾT TRUYỆN — đây là đoạn cuối cùng. "
                    "Kể xong rồi hỏi bé muốn nghe truyện khác không. "
                    "KHÔNG ĐƯỢC bịa thêm.]"
                )

            # Save state for next "kể tiếp"
            # Backup current state so barge-in can rollback
            self._rag_story_state_backup = dict(
                getattr(self, "_rag_story_state", {}) or {}
            )
            if new_sub_offset > 0:
                self._rag_story_state = {
                    "story_id": matched_story_id,
                    "doc_id": doc_id,
                    "last_part_index": last_read_index,
                    "total_parts": total_parts,
                    "sub_offset": new_sub_offset,
                }
            else:
                self._rag_story_state = {
                    "story_id": matched_story_id,
                    "doc_id": doc_id,
                    "last_part_index": last_read_index,
                    "total_parts": total_parts,
                    "sub_offset": 0,
                }

            if not is_continue and matched_story_id:
                self._push_mentioned_story(matched_story_id)
                self._last_suggested_stories = []

            if is_continue:
                template = (
                    "[TRUYỆN TỪ KHO — TIẾP TỤC]\n{context}\n[HẾT]\n"
                    "RÀNG BUỘC: Kể ĐÚNG nội dung trên, THEO THỨ TỰ. "
                    "KHÔNG lặp lại đoạn đã kể. KHÔNG bịa thêm sự kiện. "
                    "KHÔNG nhảy qua đoạn nào.\n"
                    "Khi kể xong, KẾT THÚC bằng thẻ [DONE_SENTENCE: N] "
                    "trong đó N là số thứ tự câu cuối bạn đã kể."
                )
            else:
                template = rag_inline_config.get(
                    "context_template",
                    "[TRUYỆN TỪ KHO]\n{context}\n[HẾT]\n"
                    "Quy tắc: Kể ĐÚNG truyện bé hỏi. KHÔNG bịa sự kiện/địa danh.\n"
                    "Khi kể xong, KẾT THÚC bằng thẻ [DONE_SENTENCE: N] "
                    "trong đó N là số thứ tự câu cuối bạn đã kể.",
                )
            progress = f"{start_index+1}-{last_read_index+1}/{total_parts}"
            sub_label = ""
            if new_sub_offset > 0:
                sub_label = "a"
            elif sub_offset > 0:
                sub_label = "b"
            try:
                context = template.format(
                    context=full_text,
                    part_progress=f"{progress}{sub_label}",
                )
            except KeyError:
                context = template.format(context=full_text)

            self.logger.bind(tag=TAG).info(
                f"RAG Inline: story='{matched_story_id}' parts=[{progress}{sub_label}] "
                f"chars={len(full_text)} sub_offset={sub_offset}->{new_sub_offset} "
                f"doc_id={doc_id[:8]}..."
            )
            return context

        except asyncio.TimeoutError:
            self.logger.bind(tag=TAG).warning(
                f"RAG Inline: search timeout for query: {query[:50]}"
            )
            return ""
        except Exception as e:
            self.logger.bind(tag=TAG).warning(
                f"RAG Inline: search failed [{type(e).__name__}]: {e}"
            )
            return ""

    def _merge_tool_calls(self, tool_calls_list, tools_call):
        """合并工具调用列表

        Args:
            tool_calls_list: 已收集的工具调用列表
            tools_call: 新的工具调用
        """
        for tool_call in tools_call:
            tool_index = getattr(tool_call, "index", None)
            if tool_index is None:
                if tool_call.function.name:
                    # 有 function_name，说明是新的工具调用
                    tool_index = len(tool_calls_list)
                else:
                    tool_index = len(tool_calls_list) - 1 if tool_calls_list else 0

            # 确保列表有足够的位置
            if tool_index >= len(tool_calls_list):
                tool_calls_list.append({"id": "", "name": "", "arguments": ""})

            # 更新工具调用信息
            if tool_call.id:
                tool_calls_list[tool_index]["id"] = tool_call.id
            if tool_call.function.name:
                tool_calls_list[tool_index]["name"] = tool_call.function.name
            if tool_call.function.arguments:
                tool_calls_list[tool_index]["arguments"] += tool_call.function.arguments
