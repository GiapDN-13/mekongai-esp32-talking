import asyncio
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler
from core.api.rag_handler import RAGHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)
        try:
            self.rag_handler = RAGHandler(config)
        except Exception as e:
            self.logger.bind(tag=TAG).warning(
                f"RAGHandler init failed (KB API unavailable): {e}"
            )
            self.rag_handler = None

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """Get WebSocket URL.

        Returns the user-configured URL if it looks valid,
        otherwise auto-generates from local IP and port.
        """
        server_config = self.config["server"]
        websocket_config = (server_config.get("websocket") or "").strip()

        # Detect placeholder/default values that haven't been customized
        if websocket_config and not any(
            marker in websocket_config
            for marker in ("your-", "你", "domain", "ip-or", "端口")
        ):
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))

            if port:
                app = web.Application()

                if not read_config_from_api:
                    # 如果没有开启智控台，只是单模块运行，就需要再添加简单OTA接口，用于下发websocket接口
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            # 下载接口，仅提供 data/bin/*.bin 下载
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                # 添加路由
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                    ]
                )

                # RAG Knowledge Base API routes (cho manager-web UI)
                if self.rag_handler:
                    app.add_routes([
                        web.get("/datasets/rag-models", self.rag_handler.get_rag_models),
                        web.options("/datasets/rag-models", self.rag_handler.handle_options),
                        web.get("/datasets/rag-readiness", self.rag_handler.rag_readiness),
                        web.options("/datasets/rag-readiness", self.rag_handler.handle_options),
                        web.get("/datasets", self.rag_handler.list_datasets),
                        web.post("/datasets", self.rag_handler.create_dataset),
                        web.put("/datasets/{dataset_id}", self.rag_handler.update_dataset),
                        web.delete("/datasets/{dataset_id}", self.rag_handler.delete_dataset),
                        web.delete("/datasets/batch", self.rag_handler.batch_delete_datasets),
                        web.get("/datasets/{dataset_id}/documents", self.rag_handler.list_documents),
                        web.post("/datasets/{dataset_id}/documents", self.rag_handler.upload_document),
                        web.delete(
                            "/datasets/{dataset_id}/documents/{doc_id}",
                            self.rag_handler.delete_document,
                        ),
                        web.post("/datasets/{dataset_id}/chunks", self.rag_handler.parse_documents),
                        web.get(
                            "/datasets/{dataset_id}/documents/{doc_id}/chunks",
                            self.rag_handler.list_chunks,
                        ),
                        web.post(
                            "/datasets/{dataset_id}/retrieval-test",
                            self.rag_handler.retrieval_test,
                        ),
                        web.options("/datasets", self.rag_handler.handle_options),
                        web.options("/datasets/{dataset_id}", self.rag_handler.handle_options),
                        web.options("/datasets/batch", self.rag_handler.handle_options),
                        web.options("/datasets/{dataset_id}/documents", self.rag_handler.handle_options),
                        web.options(
                            "/datasets/{dataset_id}/documents/{doc_id}",
                            self.rag_handler.handle_options,
                        ),
                        web.options("/datasets/{dataset_id}/chunks", self.rag_handler.handle_options),
                        web.options(
                            "/datasets/{dataset_id}/documents/{doc_id}/chunks",
                            self.rag_handler.handle_options,
                        ),
                        web.options(
                            "/datasets/{dataset_id}/retrieval-test",
                            self.rag_handler.handle_options,
                        ),
                    ])
                    self.logger.bind(tag=TAG).info(
                        "RAG Knowledge Base API routes registered at /datasets"
                    )
                else:
                    self.logger.bind(tag=TAG).warning(
                        "RAG routes NOT registered (RAGHandler init failed)"
                    )

                # 运行服务
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, host, port)
                await site.start()

                # 保持服务运行
                while True:
                    await asyncio.sleep(3600)  # 每隔 1 小时检查一次
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP server failed to start: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"Stack trace: {traceback.format_exc()}")
            raise
