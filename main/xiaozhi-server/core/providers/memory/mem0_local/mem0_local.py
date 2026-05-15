import json
import traceback

from ..base import MemoryProviderBase, logger

TAG = __name__


class MemoryProvider(MemoryProviderBase):
    """Long-term memory provider using Mem0 OSS SDK + Qdrant vector store."""

    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        self.use_mem0 = False

        try:
            from mem0 import Memory

            mem0_config = self._build_mem0_config(config)

            self.client = Memory.from_config(mem0_config)
            self.use_mem0 = True
            logger.bind(tag=TAG).info(
                "Mem0 Local (OSS + Qdrant) initialized"
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Mem0 Local init error: {e}")
            logger.bind(tag=TAG).error(f"Detail: {traceback.format_exc()}")

    def _build_mem0_config(self, config):
        """Build mem0 config from either YAML nested format or UI flat format."""
        # If config already has nested format (from config.yaml), use directly
        if "vector_store" in config and "embedder" in config:
            mem0_config = {
                "vector_store": config["vector_store"],
                "embedder": config["embedder"],
            }

            # Fill empty Bedrock credentials from global config (sys_params via API)
            embedder_cfg = mem0_config["embedder"].get("config", {})
            if mem0_config["embedder"].get("provider") == "aws_bedrock":
                if not embedder_cfg.get("aws_access_key_id"):
                    embedder_cfg["aws_access_key_id"] = config.get("bedrock_access_key", "")
                if not embedder_cfg.get("aws_secret_access_key"):
                    embedder_cfg["aws_secret_access_key"] = config.get("bedrock_secret_key", "")
                if not embedder_cfg.get("aws_region"):
                    embedder_cfg["aws_region"] = config.get("bedrock_region", "us-east-1")

            llm_cfg = config.get("llm")
            if llm_cfg:
                mem0_config["llm"] = llm_cfg
                # Fill empty Bedrock credentials for LLM too
                llm_inner = mem0_config["llm"].get("config", {})
                if mem0_config["llm"].get("provider") == "aws_bedrock":
                    if not llm_inner.get("aws_access_key_id"):
                        llm_inner["aws_access_key_id"] = config.get("bedrock_access_key", "")
                    if not llm_inner.get("aws_secret_access_key"):
                        llm_inner["aws_secret_access_key"] = config.get("bedrock_secret_key", "")
                    if not llm_inner.get("aws_region"):
                        llm_inner["aws_region"] = config.get("bedrock_region", "us-east-1")
            return mem0_config

        # Flat format from UI configJson
        qdrant_host = config.get("qdrant_host", "localhost")
        qdrant_port = int(config.get("qdrant_port", 6333))
        collection_name = config.get("collection_name", "xiaozhi_memory_v2")

        embedder_provider = config.get("embedder_provider", "aws_bedrock")
        embedding_model = config.get("embedding_model", "amazon.titan-embed-text-v2:0")

        embedder_config = {"model": embedding_model}

        if embedder_provider == "aws_bedrock":
            embedder_config["aws_region"] = config.get("aws_region", "us-east-1")
            if config.get("aws_access_key_id"):
                embedder_config["aws_access_key_id"] = config["aws_access_key_id"]
            if config.get("aws_secret_access_key"):
                embedder_config["aws_secret_access_key"] = config["aws_secret_access_key"]
        elif embedder_provider == "openai":
            if config.get("openai_api_key"):
                embedder_config["api_key"] = config["openai_api_key"]

        mem0_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": qdrant_host,
                    "port": qdrant_port,
                    "collection_name": collection_name,
                },
            },
            "embedder": {
                "provider": embedder_provider,
                "config": embedder_config,
            },
        }

        llm_cfg = config.get("llm")
        if llm_cfg:
            mem0_config["llm"] = llm_cfg

        return mem0_config

    async def save_memory(self, msgs, session_id=None):
        if not self.use_mem0:
            return None
        if len(msgs) < 2:
            return None

        try:
            messages = []
            for message in msgs:
                if message.role == "system":
                    continue

                content = message.content
                try:
                    if (
                        content
                        and content.strip().startswith("{")
                        and content.strip().endswith("}")
                    ):
                        data = json.loads(content)
                        if "content" in data:
                            content = data["content"]
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

                messages.append({"role": message.role, "content": content})

            result = self.client.add(messages, user_id=self.role_id)
            logger.bind(tag=TAG).info(f"Mem0 Local saved {len(messages)} messages -> {result}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Mem0 Local save error: {e}")
            return None

    async def query_memory(self, query: str) -> str:
        if not self.use_mem0:
            return ""
        try:
            if not getattr(self, "role_id", None):
                return ""

            search_query = query
            try:
                if query.strip().startswith("{") and query.strip().endswith("}"):
                    data = json.loads(query)
                    if "content" in data:
                        search_query = data["content"]
            except (json.JSONDecodeError, KeyError):
                pass

            results = self.client.search(search_query, user_id=self.role_id)

            if not results or not isinstance(results, list):
                if isinstance(results, dict) and "results" in results:
                    results = results["results"]
                else:
                    return ""

            memories = []
            for entry in results:
                if isinstance(entry, dict):
                    memory = entry.get("memory", "")
                    if memory:
                        memories.append(f"- {memory}")

            if not memories:
                return ""

            result_str = "\n".join(memories)
            logger.bind(tag=TAG).debug(f"Mem0 Local query results: {result_str}")
            return result_str
        except Exception as e:
            logger.bind(tag=TAG).error(f"Mem0 Local query error: {e}")
            return ""
